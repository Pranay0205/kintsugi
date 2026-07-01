package main

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"sort"
	"strconv"
	"strings"
)

// ---------------------------------------------------------------------------
// GET /api/class
// ---------------------------------------------------------------------------

type KCEntry struct {
	KC           string `json:"kc"`
	Kind         string `json:"kind"`
	GapCount     int    `json:"gap_count"`
	StudentCount int    `json:"student_count"`
}

func handleClass(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		rows, err := db.Query(`
			SELECT k.name, k.kind,
			       COUNT(sg.submission_id)              AS gap_count,
			       COUNT(DISTINCT sub.student_id)       AS student_count
			FROM kcs k
			LEFT JOIN submission_gaps sg ON sg.kc = k.name
			LEFT JOIN submissions sub    ON sub.id = sg.submission_id AND sub.source = 'study'
			GROUP BY k.name, k.kind
			ORDER BY gap_count DESC
		`)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()

		var out []KCEntry
		for rows.Next() {
			var e KCEntry
			rows.Scan(&e.KC, &e.Kind, &e.GapCount, &e.StudentCount)
			out = append(out, e)
		}
		writeJSON(w, out)
	}
}

// ---------------------------------------------------------------------------
// GET /api/students
// ---------------------------------------------------------------------------

type StudentSummary struct {
	ID          int      `json:"id"`
	Cluster     string   `json:"cluster"`
	Sub100Count int      `json:"sub100_count"`
	TopGaps     []string `json:"top_gaps"`
	RankScore   float64  `json:"rank_score"`
}

func handleStudents(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Load recurrence lookup: (kc, cluster) → hit_rate
		recur := loadRecurrence(db)

		students, err := allStudents(db)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}

		var out []StudentSummary
		for _, s := range students {
			sub100, gapCounts, err := studentGapCounts(db, s.ID)
			if err != nil {
				continue
			}

			rankScore := 0.0
			for kc, cnt := range gapCounts {
				if hr, ok := recur[kc+"::"+s.Cluster]; ok {
					rankScore += float64(cnt) * hr
				} else if hr, ok := recur[kc+"::struggling"]; ok {
					rankScore += float64(cnt) * hr
				}
			}

			top := topKs(gapCounts, 3)
			out = append(out, StudentSummary{
				ID:          s.ID,
				Cluster:     s.Cluster,
				Sub100Count: sub100,
				TopGaps:     top,
				RankScore:   rankScore,
			})
		}

		sort.Slice(out, func(i, j int) bool {
			return out[i].RankScore > out[j].RankScore
		})
		writeJSON(w, out)
	}
}

// ---------------------------------------------------------------------------
// GET /api/student/{id}
// ---------------------------------------------------------------------------

type Flag struct {
	ProblemID    int      `json:"problem_id"`
	Score        float64  `json:"score"`
	AttemptOrder int      `json:"attempt_order"`
	RequiredKCs  []string `json:"required_kcs"`
	Gaps         []string `json:"gaps"`
	Reasoning    string   `json:"reasoning"`
	Code         string   `json:"code"`
	Source       string   `json:"source"`
}

type TrajectoryPoint struct {
	KC           string `json:"kc"`
	AttemptOrder int    `json:"attempt_order"`
	Failed       bool   `json:"failed"`
}

type SubmissionStat struct {
	AttemptOrder int     `json:"attempt_order"`
	Score        float64 `json:"score"`
	GapCount     int     `json:"gap_count"`
}

type StudentDetail struct {
	ID          int               `json:"id"`
	Cluster     string            `json:"cluster"`
	Sub100Count int               `json:"sub100_count"`
	WeakKCs     []string          `json:"weak_kcs"`
	StrongKCs   []string          `json:"strong_kcs"`
	Flags       []Flag            `json:"flags"`
	Trajectory  []TrajectoryPoint `json:"trajectory"`
	Timeline    []SubmissionStat  `json:"timeline"`
}

func handleStudent(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		idStr := r.PathValue("id")
		sid, err := strconv.Atoi(idStr)
		if err != nil {
			http.Error(w, "bad id", 400)
			return
		}

		var cluster string
		if err := db.QueryRow("SELECT cluster FROM students WHERE id = ?", sid).Scan(&cluster); err != nil {
			http.Error(w, "student not found", 404)
			return
		}

		sub100, gapCounts, err := studentGapCounts(db, sid)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}

		// weak KCs: flagged at least once
		var weakKCs []string
		for kc := range gapCounts {
			weakKCs = append(weakKCs, kc)
		}
		sort.Strings(weakKCs)

		// strong KCs: tested (in problem_kcs for attempted problems) but never flagged
		strongKCs := strongKCsForStudent(db, sid, gapCounts)

		// flags: non-perfect submissions with their gaps
		flags := flagsForStudent(db, sid)

		// trajectory
		traj := trajectoryForStudent(db, sid)

		// timeline: all submissions with gap count per attempt
		timeline := timelineForStudent(db, sid)

		writeJSON(w, StudentDetail{
			ID:          sid,
			Cluster:     cluster,
			Sub100Count: sub100,
			WeakKCs:     weakKCs,
			StrongKCs:   strongKCs,
			Flags:       flags,
			Trajectory:  traj,
			Timeline:    timeline,
		})
	}
}

// ---------------------------------------------------------------------------
// GET /api/problems
// ---------------------------------------------------------------------------

type ProblemInfo struct {
	ID           int      `json:"id"`
	AssignmentID int      `json:"assignment_id"`
	Requirement  string   `json:"requirement"`
	RequiredKCs  []string `json:"required_kcs"`
}

func handleProblems(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		rows, err := db.Query(`
			SELECT p.id, p.assignment_id, p.requirement, COALESCE(group_concat(pk.kc, ','), '') as kcs
			FROM problems p
			LEFT JOIN problem_kcs pk ON pk.problem_id = p.id
			GROUP BY p.id
			ORDER BY p.assignment_id, p.id
		`)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()

		var out []ProblemInfo
		for rows.Next() {
			var p ProblemInfo
			var kcsRaw string
			rows.Scan(&p.ID, &p.AssignmentID, &p.Requirement, &kcsRaw)
			if kcsRaw != "" {
				for _, kc := range strings.Split(kcsRaw, ",") {
					p.RequiredKCs = append(p.RequiredKCs, strings.TrimSpace(kc))
				}
			}
			out = append(out, p)
		}
		writeJSON(w, out)
	}
}

// ---------------------------------------------------------------------------
// GET /api/practice?kc=X
// ---------------------------------------------------------------------------

type PracticeItem struct {
	ProblemID    int `json:"problem_id"`
	AssignmentID int `json:"assignment_id"`
}

func handlePractice(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		kc := r.URL.Query().Get("kc")
		if kc == "" {
			http.Error(w, "kc required", 400)
			return
		}
		rows, err := db.Query(`
			SELECT DISTINCT p.id, p.assignment_id
			FROM problems p
			JOIN problem_kcs pk ON pk.problem_id = p.id
			WHERE pk.kc = ?
			ORDER BY p.assignment_id, p.id
		`, kc)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()

		var out []PracticeItem
		for rows.Next() {
			var item PracticeItem
			rows.Scan(&item.ProblemID, &item.AssignmentID)
			out = append(out, item)
		}
		writeJSON(w, out)
	}
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

type studentRow struct {
	ID      int
	Cluster string
}

func allStudents(db *sql.DB) ([]studentRow, error) {
	rows, err := db.Query("SELECT id, cluster FROM students")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []studentRow
	for rows.Next() {
		var s studentRow
		rows.Scan(&s.ID, &s.Cluster)
		out = append(out, s)
	}
	return out, nil
}

func studentGapCounts(db *sql.DB, sid int) (sub100 int, gapCounts map[string]int, err error) {
	db.QueryRow(`
		SELECT COUNT(*) FROM submissions
		WHERE student_id = ? AND score < 1.0 AND source = 'study'
	`, sid).Scan(&sub100)

	rows, err := db.Query(`
		SELECT sg.kc, COUNT(*) as cnt
		FROM submission_gaps sg
		JOIN submissions sub ON sub.id = sg.submission_id
		WHERE sub.student_id = ? AND sub.source = 'study'
		GROUP BY sg.kc
	`, sid)
	if err != nil {
		return 0, nil, err
	}
	defer rows.Close()

	gapCounts = map[string]int{}
	for rows.Next() {
		var kc string
		var cnt int
		rows.Scan(&kc, &cnt)
		gapCounts[kc] = cnt
	}
	return
}

func loadRecurrence(db *sql.DB) map[string]float64 {
	rows, _ := db.Query("SELECT kc, cluster, hit_rate FROM recurrence")
	defer rows.Close()
	m := map[string]float64{}
	for rows.Next() {
		var kc, cluster string
		var hr float64
		rows.Scan(&kc, &cluster, &hr)
		m[kc+"::"+cluster] = hr
	}
	return m
}

func topKs(counts map[string]int, n int) []string {
	type kv struct{ k string; v int }
	var pairs []kv
	for k, v := range counts {
		pairs = append(pairs, kv{k, v})
	}
	sort.Slice(pairs, func(i, j int) bool { return pairs[i].v > pairs[j].v })
	var out []string
	for i, p := range pairs {
		if i >= n {
			break
		}
		out = append(out, p.k)
	}
	return out
}

func strongKCsForStudent(db *sql.DB, sid int, weak map[string]int) []string {
	rows, err := db.Query(`
		SELECT DISTINCT pk.kc
		FROM problem_kcs pk
		JOIN submissions sub ON sub.problem_id = pk.problem_id
		WHERE sub.student_id = ? AND sub.source = 'study'
	`, sid)
	if err != nil {
		return nil
	}
	defer rows.Close()

	var out []string
	seen := map[string]bool{}
	for rows.Next() {
		var kc string
		rows.Scan(&kc)
		if weak[kc] == 0 && !seen[kc] {
			out = append(out, kc)
			seen[kc] = true
		}
	}
	sort.Strings(out)
	return out
}

func flagsForStudent(db *sql.DB, sid int) []Flag {
	// Load all submissions first (closes cursor before sub-queries)
	type rawSub struct {
		id           int
		problemID    int
		score        float64
		attemptOrder int
		reasoning    string
		code         string
		source       string
	}
	var raws []rawSub
	{
		rows, err := db.Query(`
			SELECT sub.id, sub.problem_id, sub.score, sub.attempt_order,
			       sub.reasoning, sub.code, sub.source
			FROM submissions sub
			WHERE sub.student_id = ? AND sub.score < 1.0
			ORDER BY sub.attempt_order
		`, sid)
		if err != nil {
			return nil
		}
		for rows.Next() {
			var r rawSub
			rows.Scan(&r.id, &r.problemID, &r.score, &r.attemptOrder,
				&r.reasoning, &r.code, &r.source)
			raws = append(raws, r)
		}
		rows.Close()
	}

	// Batch load problem KCs and gaps
	problemKCs := make(map[int][]string)
	subGaps := make(map[int][]string)
	for _, r := range raws {
		if _, seen := problemKCs[r.problemID]; !seen {
			var kcs []string
			krows, _ := db.Query("SELECT kc FROM problem_kcs WHERE problem_id = ?", r.problemID)
			for krows.Next() {
				var kc string
				krows.Scan(&kc)
				kcs = append(kcs, kc)
			}
			krows.Close()
			problemKCs[r.problemID] = kcs
		}
		var gaps []string
		grows, _ := db.Query("SELECT kc FROM submission_gaps WHERE submission_id = ?", r.id)
		for grows.Next() {
			var kc string
			grows.Scan(&kc)
			gaps = append(gaps, kc)
		}
		grows.Close()
		subGaps[r.id] = gaps
	}

	var flags []Flag
	for _, r := range raws {
		flags = append(flags, Flag{
			ProblemID:    r.problemID,
			Score:        r.score,
			AttemptOrder: r.attemptOrder,
			RequiredKCs:  problemKCs[r.problemID],
			Gaps:         subGaps[r.id],
			Reasoning:    r.reasoning,
			Code:         r.code,
			Source:       r.source,
		})
	}
	return flags
}

func trajectoryForStudent(db *sql.DB, sid int) []TrajectoryPoint {
	// Single join query: no nested cursor issue
	rows, err := db.Query(`
		SELECT sub.attempt_order, sg.kc
		FROM submissions sub
		JOIN submission_gaps sg ON sg.submission_id = sub.id
		WHERE sub.student_id = ? AND sub.source = 'study'
		ORDER BY sub.attempt_order
	`, sid)
	if err != nil {
		return nil
	}
	defer rows.Close()

	var traj []TrajectoryPoint
	for rows.Next() {
		var order int
		var kc string
		rows.Scan(&order, &kc)
		traj = append(traj, TrajectoryPoint{KC: kc, AttemptOrder: order, Failed: true})
	}
	return traj
}

func timelineForStudent(db *sql.DB, sid int) []SubmissionStat {
	rows, err := db.Query(`
		SELECT sub.attempt_order, sub.score, COUNT(sg.kc) as gap_count
		FROM submissions sub
		LEFT JOIN submission_gaps sg ON sg.submission_id = sub.id
		WHERE sub.student_id = ? AND sub.source = 'study'
		GROUP BY sub.id, sub.attempt_order, sub.score
		ORDER BY sub.attempt_order
	`, sid)
	if err != nil {
		return nil
	}
	defer rows.Close()

	var out []SubmissionStat
	for rows.Next() {
		var s SubmissionStat
		rows.Scan(&s.AttemptOrder, &s.Score, &s.GapCount)
		out = append(out, s)
	}
	return out
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(v)
}
