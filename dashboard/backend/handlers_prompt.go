package main

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"strconv"
	"strings"
)

// ---------------------------------------------------------------------------
// Prompt admin — the V3 diagnosis prompt broken into editable pieces:
//   - prompt_components: free-text sections (see schema.go for the 9 keys)
//   - disambiguation_rules: the ordered rule list injected into component 6
//   - kcs (handlers_kcs.go): the KC definition table injected after component 2
// GET /api/prompt/preview renders the full assembled prompt with sample data.
// ---------------------------------------------------------------------------

type PromptComponent struct {
	Key       string `json:"key"`
	Label     string `json:"label"`
	Content   string `json:"content"`
	SortOrder int    `json:"sort_order"`
}

type DisambiguationRule struct {
	ID        int    `json:"id"`
	Rule      string `json:"rule"`
	SortOrder int    `json:"sort_order"`
}

func handlePromptComponents(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		rows, err := db.Query(`SELECT key, label, content, sort_order FROM prompt_components ORDER BY sort_order`)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()

		var out []PromptComponent
		for rows.Next() {
			var c PromptComponent
			rows.Scan(&c.Key, &c.Label, &c.Content, &c.SortOrder)
			out = append(out, c)
		}
		writeJSON(w, out)
	}
}

func handlePromptComponentByKey(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPut {
			http.Error(w, "method not allowed", 405)
			return
		}
		key := r.PathValue("key")
		var req struct {
			Content string `json:"content"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "bad body", 400)
			return
		}
		res, err := db.Exec(`UPDATE prompt_components SET content = ? WHERE key = ?`, req.Content, key)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		if n, _ := res.RowsAffected(); n == 0 {
			http.Error(w, "component not found", 404)
			return
		}
		writeJSON(w, map[string]string{"key": key, "content": req.Content})
	}
}

func handleDisambiguationRules(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			rows, err := db.Query(`SELECT id, rule, sort_order FROM disambiguation_rules ORDER BY sort_order`)
			if err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			defer rows.Close()
			var out []DisambiguationRule
			for rows.Next() {
				var d DisambiguationRule
				rows.Scan(&d.ID, &d.Rule, &d.SortOrder)
				out = append(out, d)
			}
			writeJSON(w, out)
		case http.MethodPost:
			var req struct {
				Rule string `json:"rule"`
			}
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil || strings.TrimSpace(req.Rule) == "" {
				http.Error(w, "rule required", 400)
				return
			}
			var maxOrder int
			db.QueryRow(`SELECT COALESCE(MAX(sort_order), -1) FROM disambiguation_rules`).Scan(&maxOrder)
			cursor, err := db.Exec(`INSERT INTO disambiguation_rules (rule, sort_order) VALUES (?, ?)`, req.Rule, maxOrder+1)
			if err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			id, _ := cursor.LastInsertId()
			writeJSON(w, DisambiguationRule{ID: int(id), Rule: req.Rule, SortOrder: maxOrder + 1})
		default:
			http.Error(w, "method not allowed", 405)
		}
	}
}

func handleDisambiguationRuleByID(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.Atoi(r.PathValue("id"))
		if err != nil {
			http.Error(w, "bad id", 400)
			return
		}
		switch r.Method {
		case http.MethodPut:
			var req struct {
				Rule string `json:"rule"`
			}
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				http.Error(w, "bad body", 400)
				return
			}
			res, err := db.Exec(`UPDATE disambiguation_rules SET rule = ? WHERE id = ?`, req.Rule, id)
			if err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			if n, _ := res.RowsAffected(); n == 0 {
				http.Error(w, "rule not found", 404)
				return
			}
			writeJSON(w, DisambiguationRule{ID: id, Rule: req.Rule})
		case http.MethodDelete:
			res, err := db.Exec(`DELETE FROM disambiguation_rules WHERE id = ?`, id)
			if err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			if n, _ := res.RowsAffected(); n == 0 {
				http.Error(w, "rule not found", 404)
				return
			}
			w.WriteHeader(http.StatusNoContent)
		default:
			http.Error(w, "method not allowed", 405)
		}
	}
}

func handlePromptPreview(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		sample := buildV3Prompt(db, 101, "Write a method that returns true if a year is a leap year.", 3,
			[]string{"If/Else", "LogicAndNotOr", "Math%"}, "public boolean isLeap(int year) {\n  return year % 4 == 0;\n}", 0.5)
		writeJSON(w, map[string]string{"prompt": sample})
	}
}
