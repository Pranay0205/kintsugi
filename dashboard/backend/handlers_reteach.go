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
// POST /api/reteach — AI-generated reteach plan for flagged KCs
// ---------------------------------------------------------------------------

type ReteachKCInput struct {
	KC           string `json:"kc"`
	Flags        int    `json:"flags"`
	StudentCount int    `json:"student_count"`
	TotalStudents int   `json:"total_students"`
	Kind         string `json:"kind"`
}

type ReteachRequest struct {
	KCs []ReteachKCInput `json:"kcs"`
}

type ReteachRecommendation struct {
	KC            string   `json:"kc"`
	JavaTopic     string   `json:"java_topic"`
	WhyStruggle   string   `json:"why_struggle"`
	ReteachPoints []string `json:"reteach_points"`
}

type ReteachResponse struct {
	Recommendations []ReteachRecommendation `json:"recommendations"`
	ClassSummary    string                  `json:"class_summary"`
}

func handleReteach(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req ReteachRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil || len(req.KCs) == 0 {
			http.Error(w, "bad body", 400)
			return
		}

		prompt := buildReteachPrompt(req.KCs)

		apiKey := os.Getenv("DEEPSEEK_API_KEY")
		if apiKey == "" {
			http.Error(w, "no_api_key", 500)
			return
		}

		body, _ := json.Marshal(dsRequest{
			Model:       "deepseek-chat",
			Temperature: 0.4,
			Messages:    []dsMessage{{Role: "user", Content: prompt}},
		})

		httpReq, _ := http.NewRequest("POST", "https://api.deepseek.com/v1/chat/completions", bytes.NewReader(body))
		httpReq.Header.Set("Authorization", "Bearer "+apiKey)
		httpReq.Header.Set("Content-Type", "application/json")

		client := &http.Client{Timeout: 90 * time.Second}
		resp, err := client.Do(httpReq)
		if err != nil {
			http.Error(w, "api_error", 500)
			return
		}
		defer resp.Body.Close()

		raw, _ := io.ReadAll(resp.Body)
		var dsResp dsResponse
		if err := json.Unmarshal(raw, &dsResp); err != nil || len(dsResp.Choices) == 0 {
			http.Error(w, "api_error", 500)
			return
		}

		content := strings.TrimSpace(dsResp.Choices[0].Message.Content)
		if strings.HasPrefix(content, "```") {
			lines := strings.SplitN(content, "\n", 2)
			if len(lines) > 1 {
				content = lines[1]
			}
			if idx := strings.LastIndex(content, "```"); idx >= 0 {
				content = content[:idx]
			}
			content = strings.TrimSpace(content)
		}

		var result ReteachResponse
		if err := json.Unmarshal([]byte(content), &result); err != nil {
			http.Error(w, "parse_error: "+err.Error(), 500)
			return
		}

		for i := range result.Recommendations {
			if result.Recommendations[i].ReteachPoints == nil {
				result.Recommendations[i].ReteachPoints = []string{}
			}
		}

		writeJSON(w, result)
	}
}

func buildReteachPrompt(kcs []ReteachKCInput) string {
	var kcLines []string
	for _, k := range kcs {
		kcLines = append(kcLines, fmt.Sprintf(
			`  - %s: %d flags across %d/%d students (%s KC)`,
			k.KC, k.Flags, k.StudentCount, k.TotalStudents, k.Kind,
		))
	}

	return fmt.Sprintf(`You are an expert CS1 Java instructor. The following Knowledge Components (KCs) have been flagged as class-wide gaps that need re-teaching before moving on.

KC DEFINITIONS (for reference):
- LogicCompareNum: numeric comparison bugs (wrong operator, off-by-one at boundary, enumeration instead of range)
- LogicAndNotOr: compound boolean bugs (wrong && vs ||, bad negation with !)
- LogicBoolean: boolean misuse (assignment vs comparison, redundant bool==true)
- If/Else: wrong branching structure (missing branch, wrong order of tests)
- NestedIf: incorrect nested conditional structure
- While: wrong loop structure (bad stopping condition, missing update, infinite loop)
- For: wrong loop setup (bad init, wrong update, wrong termination)
- NestedFor: incorrect nested loop structure
- Math+-*/: wrong arithmetic operation or order of operations
- Math%%: wrong or missing modulo
- StringEqual: using == instead of .equals() on strings
- StringIndex: wrong index/position in charAt or substring
- StringLen: confusion between .length() method and .length property
- StringConcat: wrong or missing string concatenation
- StringFormat: wrong output format (spacing, separators, order)
- CharEqual: wrong character-level comparison
- ArrayIndex: wrong array index, off-by-one in array access
- DefFunction: missing or broken helper method

FLAGGED KCs:
%s

For each KC, provide:
1. java_topic: The specific Java concept to cover in class (1 sentence, concrete)
2. why_struggle: Why CS1 students typically get this wrong (1-2 sentences, root cause)
3. reteach_points: 3 concrete activities or teaching points (each under 20 words)

Also provide a class_summary: 2-3 sentence overall teaching priority and recommended lesson order.

Respond with ONLY valid JSON:
{
  "recommendations": [
    {
      "kc": "KC_NAME",
      "java_topic": "...",
      "why_struggle": "...",
      "reteach_points": ["...", "...", "..."]
    }
  ],
  "class_summary": "..."
}`, strings.Join(kcLines, "\n"))
}
