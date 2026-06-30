package main

import (
	"database/sql"
	"net/http"
)

// ---------------------------------------------------------------------------
// GET /api/class/matrix
// Per-student, per-KC gap counts — used for the student×KC heatmap.
// ---------------------------------------------------------------------------

type MatrixCell struct {
	StudentID int    `json:"student_id"`
	KC        string `json:"kc"`
	GapCount  int    `json:"gap_count"`
}

func handleClassMatrix(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		rows, err := db.Query(`
			SELECT sub.student_id, sg.kc, COUNT(*) as gap_count
			FROM submission_gaps sg
			JOIN submissions sub ON sub.id = sg.submission_id
			WHERE sub.source = 'study'
			GROUP BY sub.student_id, sg.kc
			ORDER BY sub.student_id, sg.kc
		`)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()

		var out []MatrixCell
		for rows.Next() {
			var c MatrixCell
			rows.Scan(&c.StudentID, &c.KC, &c.GapCount)
			out = append(out, c)
		}
		writeJSON(w, out)
	}
}

// ---------------------------------------------------------------------------
// GET /api/class/problems
// Per-problem hardness: how many students had gaps on each problem.
// ---------------------------------------------------------------------------

type ProblemHardness struct {
	ProblemID       int `json:"problem_id"`
	AssignmentID    int `json:"assignment_id"`
	FlaggedStudents int `json:"flagged_students"`
	TotalGaps       int `json:"total_gaps"`
}

func handleClassProblems(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		rows, err := db.Query(`
			SELECT sub.problem_id, p.assignment_id,
			       COUNT(DISTINCT sub.student_id) as flagged_students,
			       COUNT(sg.kc)                  as total_gaps
			FROM submissions sub
			JOIN submission_gaps sg ON sg.submission_id = sub.id
			JOIN problems p ON p.id = sub.problem_id
			WHERE sub.source = 'study'
			GROUP BY sub.problem_id, p.assignment_id
			ORDER BY flagged_students DESC, total_gaps DESC
		`)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()

		var out []ProblemHardness
		for rows.Next() {
			var h ProblemHardness
			rows.Scan(&h.ProblemID, &h.AssignmentID, &h.FlaggedStudents, &h.TotalGaps)
			out = append(out, h)
		}
		writeJSON(w, out)
	}
}

// ---------------------------------------------------------------------------
// GET /api/class/persistence
// For each KC: of students who had it flagged, how many still had it flagged
// in the second half of their problem sequence?
// High persistence → needs explicit re-teaching, not just more practice.
// ---------------------------------------------------------------------------

type KCPersistence struct {
	KC           string  `json:"kc"`
	TotalFlagged int     `json:"total_flagged"`
	StillLate    int     `json:"still_late"`
	Persistence  float64 `json:"persistence"`
}

func handleClassPersistence(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		rows, err := db.Query(`
			WITH totals AS (
			    SELECT student_id, COUNT(*) AS cnt
			    FROM submissions
			    WHERE source = 'study'
			    GROUP BY student_id
			),
			phases AS (
			    SELECT sub.student_id, sg.kc,
			           CASE WHEN sub.attempt_order * 2 <= t.cnt THEN 'early' ELSE 'late' END AS phase
			    FROM submissions sub
			    JOIN submission_gaps sg ON sg.submission_id = sub.id
			    JOIN totals t ON t.student_id = sub.student_id
			    WHERE sub.source = 'study'
			),
			per_student AS (
			    SELECT student_id, kc,
			           MAX(CASE WHEN phase = 'early' THEN 1 ELSE 0 END) AS had_early,
			           MAX(CASE WHEN phase = 'late'  THEN 1 ELSE 0 END) AS had_late
			    FROM phases
			    GROUP BY student_id, kc
			)
			SELECT kc,
			       COUNT(*)       AS total_flagged,
			       SUM(had_late)  AS still_late
			FROM per_student
			GROUP BY kc
			HAVING total_flagged > 0
			ORDER BY CAST(SUM(had_late) AS REAL) / COUNT(*) DESC
		`)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()

		var out []KCPersistence
		for rows.Next() {
			var p KCPersistence
			rows.Scan(&p.KC, &p.TotalFlagged, &p.StillLate)
			if p.TotalFlagged > 0 {
				p.Persistence = float64(p.StillLate) / float64(p.TotalFlagged)
			}
			out = append(out, p)
		}
		writeJSON(w, out)
	}
}
