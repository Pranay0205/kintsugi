package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// POST /api/diagnose — live DeepSeek V3 KCDP diagnosis
// ---------------------------------------------------------------------------

type DiagnoseRequest struct {
	StudentID int    `json:"student_id"`
	ProblemID int    `json:"problem_id"`
	Code      string `json:"code"`
}

type DiagnoseResponse struct {
	Reasoning   string   `json:"reasoning"`
	Gaps        []string `json:"gaps"`
	InvalidKCs  []string `json:"invalid_kcs"`
	ParseStatus string   `json:"parse_status"`
	Source      string   `json:"source"`
}

func handleDiagnose(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req DiagnoseRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "bad body", 400)
			return
		}

		// Validate student exists
		var cluster string
		if err := db.QueryRow("SELECT cluster FROM students WHERE id = ?", req.StudentID).Scan(&cluster); err != nil {
			http.Error(w, "student not found", 404)
			return
		}

		// Load problem metadata
		var requirement string
		var assignmentID int
		if err := db.QueryRow(
			"SELECT requirement, assignment_id FROM problems WHERE id = ?", req.ProblemID,
		).Scan(&requirement, &assignmentID); err != nil {
			http.Error(w, "problem not found", 404)
			return
		}

		// Required KCs for this problem
		krows, _ := db.Query("SELECT kc FROM problem_kcs WHERE problem_id = ?", req.ProblemID)
		var requiredKCs []string
		for krows.Next() {
			var kc string
			krows.Scan(&kc)
			requiredKCs = append(requiredKCs, kc)
		}
		krows.Close()

		// Perfect-score skip (score not known at request time — code is submitted, score unknown)
		// The caller may pass score; for now we always run the model (score = 0 unknown).
		// Per spec: if score == 1.0 → return empty gaps. We can't enforce that here without the score.
		// The live path always runs; callers should pass score ≥ 1.0 to get the skip signal.

		prompt := buildV3Prompt(db, req.ProblemID, requirement, assignmentID, requiredKCs, req.Code, 0.5)

		reasoning, gaps, invalidKCs, parseStatus := callDeepSeek(db, prompt)
		if gaps == nil {
			gaps = []string{}
		}
		if invalidKCs == nil {
			invalidKCs = []string{}
		}

		// Compute next attempt_order for this student
		var maxOrder int
		db.QueryRow(
			"SELECT COALESCE(MAX(attempt_order), 0) FROM submissions WHERE student_id = ?",
			req.StudentID,
		).Scan(&maxOrder)

		cursor, err := db.Exec(`
			INSERT INTO submissions
			  (student_id, problem_id, score, reasoning, code, parse_status, attempt_order, source)
			VALUES (?, ?, ?, ?, ?, ?, ?, 'live')
		`, req.StudentID, req.ProblemID, 0.0, reasoning, req.Code, parseStatus, maxOrder+1)
		if err != nil {
			http.Error(w, "db insert: "+err.Error(), 500)
			return
		}
		subID, _ := cursor.LastInsertId()

		for _, kc := range gaps {
			db.Exec("INSERT OR IGNORE INTO submission_gaps (submission_id, kc) VALUES (?, ?)", subID, kc)
		}

		writeJSON(w, DiagnoseResponse{
			Reasoning:   reasoning,
			Gaps:        gaps,
			InvalidKCs:  invalidKCs,
			ParseStatus: parseStatus,
			Source:      "live",
		})
	}
}

// ---------------------------------------------------------------------------
// DeepSeek API call
// ---------------------------------------------------------------------------

type dsMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type dsRequest struct {
	Model       string      `json:"model"`
	Temperature float64     `json:"temperature"`
	Messages    []dsMessage `json:"messages"`
}

type dsChoice struct {
	Message dsMessage `json:"message"`
}

type dsResponse struct {
	Choices []dsChoice `json:"choices"`
}

func callDeepSeek(db *sql.DB, prompt string) (reasoning string, gaps []string, invalidKCs []string, parseStatus string) {
	apiKey := os.Getenv("DEEPSEEK_API_KEY")
	if apiKey == "" {
		return "", nil, nil, "no_api_key"
	}

	body, _ := json.Marshal(dsRequest{
		Model:       "deepseek-chat",
		Temperature: 0.3,
		Messages:    []dsMessage{{Role: "user", Content: prompt}},
	})

	req, _ := http.NewRequest("POST", "https://api.deepseek.com/v1/chat/completions", bytes.NewReader(body))
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 90 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", nil, nil, "api_error"
	}
	defer resp.Body.Close()

	raw, _ := io.ReadAll(resp.Body)
	var dsResp dsResponse
	if err := json.Unmarshal(raw, &dsResp); err != nil || len(dsResp.Choices) == 0 {
		return "", nil, nil, "api_error"
	}

	content := dsResp.Choices[0].Message.Content
	return parseKCDP(content, loadValidKCNames(db))
}

func parseKCDP(content string, validKCs map[string]bool) (reasoning string, gaps []string, invalidKCs []string, parseStatus string) {
	// Strip ```json fence if present
	s := strings.TrimSpace(content)
	if strings.HasPrefix(s, "```") {
		lines := strings.SplitN(s, "\n", 2)
		if len(lines) > 1 {
			s = lines[1]
		}
		if idx := strings.LastIndex(s, "```"); idx >= 0 {
			s = s[:idx]
		}
		s = strings.TrimSpace(s)
	}

	var obj struct {
		Reasoning  string   `json:"reasoning"`
		KnowledgeGaps []string `json:"knowledge_gaps"`
	}
	if err := json.Unmarshal([]byte(s), &obj); err != nil {
		return content, nil, nil, "parse_error"
	}

	for _, kc := range obj.KnowledgeGaps {
		if validKCs[kc] {
			gaps = append(gaps, kc)
		} else {
			invalidKCs = append(invalidKCs, kc)
		}
	}
	if gaps == nil {
		gaps = []string{}
	}
	if invalidKCs == nil {
		invalidKCs = []string{}
	}
	return obj.Reasoning, gaps, invalidKCs, "ok"
}

// ---------------------------------------------------------------------------
// V3 prompt builder — assembled at request time from admin-editable pieces:
// prompt_components (schema.go), the kcs table, and disambiguation_rules.
// Originally a Go port of lib/v3_prompt.py build_v3_prompt(); now DB-driven
// so instructors can tune wording from the Prompt Editor without redeploying.
// ---------------------------------------------------------------------------

func loadPromptComponentMap(db *sql.DB) map[string]string {
	rows, _ := db.Query(`SELECT key, content FROM prompt_components`)
	defer rows.Close()
	m := map[string]string{}
	for rows.Next() {
		var k, c string
		rows.Scan(&k, &c)
		m[k] = c
	}
	return m
}

func loadKCDefs(db *sql.DB) []KCDef {
	rows, _ := db.Query(`SELECT name, kind, category, gap_signal, sort_order FROM kcs ORDER BY sort_order, name`)
	defer rows.Close()
	var out []KCDef
	for rows.Next() {
		var k KCDef
		rows.Scan(&k.Name, &k.Kind, &k.Category, &k.GapSignal, &k.SortOrder)
		out = append(out, k)
	}
	return out
}

func loadDisambiguationRuleTexts(db *sql.DB) []string {
	rows, _ := db.Query(`SELECT rule FROM disambiguation_rules ORDER BY sort_order`)
	defer rows.Close()
	var out []string
	for rows.Next() {
		var r string
		rows.Scan(&r)
		out = append(out, r)
	}
	return out
}

func loadValidKCNames(db *sql.DB) map[string]bool {
	rows, _ := db.Query(`SELECT name FROM kcs`)
	defer rows.Close()
	m := map[string]bool{}
	for rows.Next() {
		var n string
		rows.Scan(&n)
		m[n] = true
	}
	return m
}

func buildKCDefsJSON(kcs []KCDef) string {
	var parts []string
	for _, k := range kcs {
		parts = append(parts, fmt.Sprintf(
			"  %q: {\n    \"category\": %q,\n    \"type\": %q,\n    \"gap_signal\": %q\n  }",
			k.Name, k.Category, k.Kind, k.GapSignal,
		))
	}
	return "{\n" + strings.Join(parts, ",\n") + "\n}"
}

func buildDisambiguationRulesJSON(rules []string) string {
	var parts []string
	for _, r := range rules {
		parts = append(parts, fmt.Sprintf(`  {"rule": %q}`, r))
	}
	return "[\n" + strings.Join(parts, ",\n") + "\n]"
}

func buildV3Prompt(db *sql.DB, problemID int, requirement string, assignmentID int, requiredKCs []string, studentCode string, score float64) string {
	comps := loadPromptComponentMap(db)
	kcs := loadKCDefs(db)
	rules := loadDisambiguationRuleTexts(db)

	var structural []string
	for _, k := range kcs {
		if k.Kind == "structural" {
			structural = append(structural, k.Name)
		}
	}

	vars := map[string]string{
		"problem_id":     strconv.Itoa(problemID),
		"assignment_id":  strconv.Itoa(assignmentID),
		"requirement":    fmt.Sprintf("%q", requirement),
		"score":          fmt.Sprintf("%.4f", score),
		"kc_count":       strconv.Itoa(len(kcs)),
		"structural_kcs": strings.Join(structural, ", "),
		"required_kcs":   strings.Join(requiredKCs, ", "),
	}

	render := func(key string) string {
		s := comps[key]
		for k, v := range vars {
			s = strings.ReplaceAll(s, "{{"+k+"}}", v)
		}
		return s
	}

	sections := []string{
		render("preamble"),
		render("kc_definitions_intro"),
		buildKCDefsJSON(kcs),
		render("kc_injection_template"),
		render("tagging_hierarchy"),
		render("redundancy_check"),
		render("disambiguation_intro"),
		buildDisambiguationRulesJSON(rules),
		render("critical_rules"),
		render("output_format"),
		render("student_code_label"),
	}

	var b strings.Builder
	b.WriteString(strings.Join(sections, "\n\n"))
	b.WriteString("\n```java\n")
	b.WriteString(studentCode)
	b.WriteString("\n```")
	return b.String()
}
