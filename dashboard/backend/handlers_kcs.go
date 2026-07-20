package main

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"strings"
)

// ---------------------------------------------------------------------------
// KC admin CRUD — GET/POST /api/kcs, PUT/DELETE /api/kcs/{name}
//
// KC names are referenced by problem_kcs.kc, submission_gaps.kc and
// recurrence.kc. Rename cascades those references; delete removes them along
// with the KC (the caller sees how many rows were affected before doing it).
// ---------------------------------------------------------------------------

type KCDef struct {
	Name      string `json:"name"`
	Kind      string `json:"kind"`
	Category  string `json:"category"`
	GapSignal string `json:"gap_signal"`
	SortOrder int    `json:"sort_order"`
}

func handleKCs(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			listKCs(db, w)
		case http.MethodPost:
			createKC(db, w, r)
		default:
			http.Error(w, "method not allowed", 405)
		}
	}
}

func listKCs(db *sql.DB, w http.ResponseWriter) {
	rows, err := db.Query(`SELECT name, kind, category, gap_signal, sort_order FROM kcs ORDER BY sort_order, name`)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()

	var out []KCDef
	for rows.Next() {
		var k KCDef
		rows.Scan(&k.Name, &k.Kind, &k.Category, &k.GapSignal, &k.SortOrder)
		out = append(out, k)
	}
	writeJSON(w, out)
}

func createKC(db *sql.DB, w http.ResponseWriter, r *http.Request) {
	var req KCDef
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad body", 400)
		return
	}
	req.Name = strings.TrimSpace(req.Name)
	if req.Name == "" {
		http.Error(w, "name required", 400)
		return
	}
	if req.Kind != "specific" && req.Kind != "structural" {
		http.Error(w, "kind must be 'specific' or 'structural'", 400)
		return
	}

	var maxOrder int
	db.QueryRow(`SELECT COALESCE(MAX(sort_order), -1) FROM kcs`).Scan(&maxOrder)

	_, err := db.Exec(
		`INSERT INTO kcs (name, kind, category, gap_signal, sort_order) VALUES (?, ?, ?, ?, ?)`,
		req.Name, req.Kind, req.Category, req.GapSignal, maxOrder+1,
	)
	if err != nil {
		http.Error(w, "a KC with that name already exists", 409)
		return
	}
	writeJSON(w, KCDef{Name: req.Name, Kind: req.Kind, Category: req.Category, GapSignal: req.GapSignal, SortOrder: maxOrder + 1})
}

func handleKCByName(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		name := r.PathValue("name")
		switch r.Method {
		case http.MethodPut:
			updateKC(db, w, r, name)
		case http.MethodDelete:
			deleteKC(db, w, name)
		default:
			http.Error(w, "method not allowed", 405)
		}
	}
}

func updateKC(db *sql.DB, w http.ResponseWriter, r *http.Request, name string) {
	var req KCDef
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad body", 400)
		return
	}
	newName := strings.TrimSpace(req.Name)
	if newName == "" {
		newName = name
	}
	if req.Kind != "specific" && req.Kind != "structural" {
		http.Error(w, "kind must be 'specific' or 'structural'", 400)
		return
	}

	var exists int
	if err := db.QueryRow(`SELECT COUNT(*) FROM kcs WHERE name = ?`, name).Scan(&exists); err != nil || exists == 0 {
		http.Error(w, "KC not found", 404)
		return
	}

	tx, err := db.Begin()
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer tx.Rollback()

	if _, err := tx.Exec(`UPDATE kcs SET name = ?, kind = ?, category = ?, gap_signal = ? WHERE name = ?`,
		newName, req.Kind, req.Category, req.GapSignal, name); err != nil {
		http.Error(w, "rename target already exists", 409)
		return
	}

	if newName != name {
		if _, err := tx.Exec(`UPDATE problem_kcs SET kc = ? WHERE kc = ?`, newName, name); err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		if _, err := tx.Exec(`UPDATE submission_gaps SET kc = ? WHERE kc = ?`, newName, name); err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		tx.Exec(`UPDATE recurrence SET kc = ? WHERE kc = ?`, newName, name) // table may not exist; ignore error
	}

	if err := tx.Commit(); err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	writeJSON(w, KCDef{Name: newName, Kind: req.Kind, Category: req.Category, GapSignal: req.GapSignal})
}

func deleteKC(db *sql.DB, w http.ResponseWriter, name string) {
	tx, err := db.Begin()
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer tx.Rollback()

	res, err := tx.Exec(`DELETE FROM kcs WHERE name = ?`, name)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	if n, _ := res.RowsAffected(); n == 0 {
		http.Error(w, "KC not found", 404)
		return
	}

	tx.Exec(`DELETE FROM problem_kcs WHERE kc = ?`, name)
	tx.Exec(`DELETE FROM submission_gaps WHERE kc = ?`, name)
	tx.Exec(`DELETE FROM recurrence WHERE kc = ?`, name) // table may not exist; ignore error

	if err := tx.Commit(); err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
