package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
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

var allKCs = map[string]bool{
	"If/Else": true, "NestedIf": true, "While": true, "For": true, "NestedFor": true,
	"Math+-*/": true, "Math%": true, "LogicAndNotOr": true, "LogicCompareNum": true,
	"LogicBoolean": true, "StringFormat": true, "StringConcat": true, "StringIndex": true,
	"StringLen": true, "StringEqual": true, "CharEqual": true, "ArrayIndex": true,
	"DefFunction": true,
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

		prompt := buildV3Prompt(req.ProblemID, requirement, assignmentID, requiredKCs, req.Code, 0.5)

		reasoning, gaps, invalidKCs, parseStatus := callDeepSeek(prompt)

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

func callDeepSeek(prompt string) (reasoning string, gaps []string, invalidKCs []string, parseStatus string) {
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
	return parseKCDP(content)
}

func parseKCDP(content string) (reasoning string, gaps []string, invalidKCs []string, parseStatus string) {
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
		if allKCs[kc] {
			gaps = append(gaps, kc)
		} else {
			invalidKCs = append(invalidKCs, kc)
		}
	}
	return obj.Reasoning, gaps, invalidKCs, "ok"
}

// ---------------------------------------------------------------------------
// V3 prompt builder — Go port of lib/v3_prompt.py build_v3_prompt()
// ---------------------------------------------------------------------------

func buildV3Prompt(problemID int, requirement string, assignmentID int, requiredKCs []string, studentCode string, score float64) string {
	kcInjection := fmt.Sprintf(
		"REQUIRED KCs FOR THIS PROBLEM: [%s]\n"+
			"These are the KCs this problem is designed to test. Check these first. "+
			"However, if the student's code reveals gaps in other KCs not on this list, tag those too.",
		strings.Join(requiredKCs, ", "),
	)

	rulesJSON := buildDisambiguationRules()

	var b strings.Builder
	fmt.Fprintf(&b, `You are an expert CS1 instructor analyzing a single student Java code submission to identify knowledge gaps.

PROBLEM CONTEXT:
{
  "problem_id": %d,
  "assignment_id": %d,
  "requirement": %q,
  "student_score": %.4f
}

KC DEFINITIONS:
Below are all 18 Knowledge Components (KCs) used in this course. Each includes what a gap looks like in student code.

{
  "If/Else": {
    "category": "Control Flow",
    "type": "structural",
    "gap_signal": "Tag when the STRUCTURE is wrong: missing branches that the problem requires, wrong order of tests, a case that is never handled, two sequential ifs where if/else was needed. Do NOT tag for missing else when a simple if-with-early-return is cleaner. Do NOT tag when the condition inside the if is wrong but the branching structure is correct — that belongs to a Logic KC."
  },
  "NestedIf": {
    "category": "Control Flow",
    "type": "structural",
    "gap_signal": "Tag only if the code actually contains nested ifs and uses them incorrectly (wrong nesting order, conditions at wrong level). Do NOT tag 'they should have nested' — only tag what the student actually wrote."
  },
  "While": {
    "category": "Loops",
    "type": "structural",
    "gap_signal": "Tag when the loop structure itself is wrong: wrong stopping condition, never updates the loop variable, infinite loop. Do NOT tag if the problem does not require a while loop and the student did not use one. Do NOT tag if the loop structure is fine but the logic inside it is wrong."
  },
  "For": {
    "category": "Loops",
    "type": "structural",
    "gap_signal": "Tag when the loop structure is wrong: wrong initialization, wrong update expression, loop variable does not iterate correctly. Off-by-one in the termination condition belongs to LogicCompareNum, not For."
  },
  "NestedFor": {
    "category": "Loops",
    "type": "structural",
    "gap_signal": "Tag only if code contains nested loops and uses them incorrectly (wrong inner bounds, reusing outer variable, wrong nesting order). Do NOT tag if the problem does not require nested loops. Do NOT infer 'the student would struggle with nested loops' — only tag what is actually in the code."
  },
  "Math+-*/": {
    "category": "Math",
    "type": "specific",
    "gap_signal": "Tag when the student uses the wrong arithmetic operation or gets arithmetic logic wrong: dividing when they should multiply, missing integer-division truncation, wrong order of operations."
  },
  "Math%%": {
    "category": "Math",
    "type": "specific",
    "gap_signal": "Tag when the student needs modulo and does not use it, or uses it wrong: checking divisibility with / instead of %%, wrong modulo base, misunderstanding what %% returns."
  },
  "LogicAndNotOr": {
    "category": "Logic",
    "type": "specific",
    "gap_signal": "Tag when the student combines booleans wrong: uses && where || was needed, inverts a condition incorrectly with !, misses a case when chaining compound conditions, wrong short-circuit logic."
  },
  "LogicCompareNum": {
    "category": "Logic",
    "type": "specific",
    "gap_signal": "Tag for any numeric comparison bug: wrong direction (< vs >), off-by-one at boundary (< vs <=), enumerating values (day==1||day==2||day==3) instead of using ranges (day>=1 && day<=5), comparing when equality was needed or vice versa."
  },
  "LogicBoolean": {
    "category": "Logic",
    "type": "specific",
    "gap_signal": "Tag for: if (x = true) (assignment instead of comparison), returning true/false in the wrong branch, unnecessary if (bool == true) revealing misunderstanding of boolean type, using 0/1 instead of true/false."
  },
  "StringFormat": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when the student cannot produce the expected output format even when their logic is close: wrong spacing, missing separators, wrong order of concatenated pieces in the final output string."
  },
  "StringConcat": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when concatenation is missing, in wrong order, or produces wrong result. Not about output format (that is StringFormat) — about the mechanical act of joining strings."
  },
  "StringIndex": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag for wrong index, index out of bounds, off-by-one in string position, using wrong substring bounds."
  },
  "StringLen": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when the student confuses .length() method with .length property (Java arrays), or uses wrong length value for substring bounds, or does not account for zero-based indexing with length."
  },
  "StringEqual": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when the student uses == on strings instead of .equals(), or compares the wrong parts of strings. Do NOT tag for numeric comparisons — that is LogicCompareNum."
  },
  "CharEqual": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when comparison at the character level is wrong: comparing wrong char position, wrong char literal, confusing char with String type."
  },
  "ArrayIndex": {
    "category": "Arrays",
    "type": "specific",
    "gap_signal": "Tag for out-of-bounds access, off-by-one in array indexing, wrong index variable, confusing index with value stored at that index."
  },
  "DefFunction": {
    "category": "Functions",
    "type": "specific",
    "gap_signal": "Tag when the problem asks for a specific helper method and the student's helper is missing, incomplete, has wrong signature, or has broken logic inside it."
  }
}

%s

TAGGING HIERARCHY — CHECK SPECIFIC BEFORE STRUCTURAL:
KCs marked "structural" (If/Else, NestedIf, While, For, NestedFor) are tags of LAST RESORT.
Always check "specific" KCs first (Logic, Math, String, Array, Function).
If a specific KC explains the error, tag ONLY the specific KC. Do NOT also tag the structural KC.
Tag a structural KC only when the structure itself is the problem and no specific KC explains it.

Examples:
- Wrong condition inside an if-statement → LogicCompareNum or LogicBoolean, NOT If/Else
- Wrong loop boundary value → LogicCompareNum, NOT For
- Wrong arithmetic inside a loop body → Math+-*/, NOT For
- Student uses && where || needed inside an if → LogicAndNotOr, NOT If/Else

REDUNDANCY CHECK — apply before finalizing your tags:
For every structural KC (If/Else, NestedIf, While, For, NestedFor) in your list, ask: "If I remove this tag, does my diagnosis lose any information?" If the answer is no — if a specific KC already explains the error — drop the structural tag.

DISAMBIGUATION RULES:
When two KCs seem applicable, use these rules to pick the correct one.

%s

CRITICAL RULES:
1. If the code is a trivial placeholder (e.g., just "return true;" or "return 0;") with no real attempt, return empty knowledge_gaps.
2. If the student scored 1.0 (perfect), return empty knowledge_gaps.
3. Only use KC names from the 18 defined above. Do not invent new names.
4. Think through your reasoning BEFORE listing gaps. Write your reasoning first, then decide on tags.

OUTPUT FORMAT:
Respond with ONLY a JSON object, no other text:
{
  "reasoning": "Brief explanation of what the student did wrong and which KCs are affected, applying the hierarchy (specific before structural).",
  "knowledge_gaps": ["KC1", "KC2"]
}

STUDENT CODE:
`, problemID, assignmentID, requirement, score, kcInjection, rulesJSON)

	b.WriteString("```java\n")
	b.WriteString(studentCode)
	b.WriteString("\n```")
	return b.String()
}

func buildDisambiguationRules() string {
	rules := []string{
		`LogicCompareNum vs If/Else — If the student writes day==1||day==2||day==3 instead of day>=1&&day<=5, tag LogicCompareNum. The if-statement structure is correct, the comparison inside it is wrong.`,
		`LogicBoolean vs If/Else — If the student writes vacation==false instead of !vacation, or uses = instead of ==, tag LogicBoolean. The student misunderstands boolean values, not branching structure.`,
		`LogicAndNotOr vs If/Else — If the student uses && where || was needed or misses parentheses on grouped conditions, tag LogicAndNotOr. The branching structure is fine, the boolean composition is wrong.`,
		`LogicCompareNum vs For — Off-by-one in a loop termination condition (< vs <=) is LogicCompareNum. The loop structure is correct, the comparison value is wrong. Tag For only when init, update, or overall structure is broken.`,
		`Math+-*/ vs For — Wrong arithmetic inside a loop body is Math+-*/. Wrong increment in the for-update (i+=1 when it should be i+=2) is For, because the update is part of loop structure.`,
		`StringEqual vs LogicCompareNum — String comparison with == or .equals() is StringEqual. Numeric comparison with <, >, == between numbers is LogicCompareNum. Never interchangeable.`,
		`CharEqual vs StringEqual — charAt() comparisons are CharEqual. Full-string .equals() comparisons are StringEqual.`,
		`StringIndex vs StringLen — Wrong position in charAt()/substring() is StringIndex. Wrong .length() usage or confusing .length with .length() is StringLen.`,
		`StringConcat vs StringFormat — Failing to join strings mechanically is StringConcat. Joining strings but producing wrong output format (spacing, separators) is StringFormat.`,
		`ArrayIndex vs LogicCompareNum — Wrong element retrieved from arr[i] due to wrong index is ArrayIndex. Wrong threshold in a comparison like if(arr[i]>5) is LogicCompareNum.`,
		`ArrayIndex vs For — Wrong array element accessed inside a correct loop is ArrayIndex. Wrong loop bounds for array iteration: check if it is the comparison value (LogicCompareNum) or the loop setup (For).`,
		`LogicCompareNum vs LogicBoolean — Comparing two numeric values (age>18) incorrectly is LogicCompareNum. Misusing a boolean value (if(x=true), redundant bool==true) is LogicBoolean.`,
		`LogicCompareNum vs LogicAndNotOr — A single comparison that is wrong (< instead of <=) is LogicCompareNum. Multiple comparisons combined with the wrong operator (&& instead of ||) is LogicAndNotOr. If both are wrong, tag both.`,
		`NestedFor vs While — Only tag the construct actually in the code. Nested for-loops wrong = NestedFor. While-loop wrong = While. Never tag a construct the student did not write.`,
	}

	var parts []string
	for _, r := range rules {
		parts = append(parts, fmt.Sprintf(`  {"rule": %q}`, r))
	}
	return "[\n" + strings.Join(parts, ",\n") + "\n]"
}
