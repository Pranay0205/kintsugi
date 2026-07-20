package main

import "database/sql"

// ---------------------------------------------------------------------------
// Schema migration + one-time seed for KC metadata and the editable V3 prompt.
// Seeding is idempotent: it only fills rows/columns that are still empty, so
// it never clobbers edits made through the admin UI on later restarts.
// ---------------------------------------------------------------------------

func ensureSchema(db *sql.DB) {
	// kcs table already exists (name, kind) from ingest.py. Extend it with
	// admin-editable metadata. SQLite errors on a duplicate column; ignore.
	db.Exec(`ALTER TABLE kcs ADD COLUMN category TEXT NOT NULL DEFAULT ''`)
	db.Exec(`ALTER TABLE kcs ADD COLUMN gap_signal TEXT NOT NULL DEFAULT ''`)
	db.Exec(`ALTER TABLE kcs ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0`)

	db.Exec(`CREATE TABLE IF NOT EXISTS disambiguation_rules (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		rule TEXT NOT NULL,
		sort_order INTEGER NOT NULL DEFAULT 0
	)`)

	db.Exec(`CREATE TABLE IF NOT EXISTS prompt_components (
		key TEXT PRIMARY KEY,
		label TEXT NOT NULL,
		content TEXT NOT NULL,
		sort_order INTEGER NOT NULL DEFAULT 0
	)`)

	seedKCMetadata(db)
	seedPromptComponents(db)
	seedDisambiguationRules(db)
}

type kcSeed struct {
	name      string
	kind      string
	category  string
	gapSignal string
}

func defaultKCSeeds() []kcSeed {
	return []kcSeed{
		{"If/Else", "structural", "Control Flow", `Tag when the STRUCTURE is wrong: missing branches that the problem requires, wrong order of tests, a case that is never handled, two sequential ifs where if/else was needed. Do NOT tag for missing else when a simple if-with-early-return is cleaner. Do NOT tag when the condition inside the if is wrong but the branching structure is correct — that belongs to a Logic KC.`},
		{"NestedIf", "structural", "Control Flow", `Tag only if the code actually contains nested ifs and uses them incorrectly (wrong nesting order, conditions at wrong level). Do NOT tag 'they should have nested' — only tag what the student actually wrote.`},
		{"While", "structural", "Loops", `Tag when the loop structure itself is wrong: wrong stopping condition, never updates the loop variable, infinite loop. Do NOT tag if the problem does not require a while loop and the student did not use one. Do NOT tag if the loop structure is fine but the logic inside it is wrong.`},
		{"For", "structural", "Loops", `Tag when the loop structure is wrong: wrong initialization, wrong update expression, loop variable does not iterate correctly. Off-by-one in the termination condition belongs to LogicCompareNum, not For.`},
		{"NestedFor", "structural", "Loops", `Tag only if code contains nested loops and uses them incorrectly (wrong inner bounds, reusing outer variable, wrong nesting order). Do NOT tag if the problem does not require nested loops. Do NOT infer 'the student would struggle with nested loops' — only tag what is actually in the code.`},
		{"Math+-*/", "specific", "Math", `Tag when the student uses the wrong arithmetic operation or gets arithmetic logic wrong: dividing when they should multiply, missing integer-division truncation, wrong order of operations.`},
		{"Math%", "specific", "Math", `Tag when the student needs modulo and does not use it, or uses it wrong: checking divisibility with / instead of %, wrong modulo base, misunderstanding what % returns.`},
		{"LogicAndNotOr", "specific", "Logic", `Tag when the student combines booleans wrong: uses && where || was needed, inverts a condition incorrectly with !, misses a case when chaining compound conditions, wrong short-circuit logic.`},
		{"LogicCompareNum", "specific", "Logic", `Tag for any numeric comparison bug: wrong direction (< vs >), off-by-one at boundary (< vs <=), enumerating values (day==1||day==2||day==3) instead of using ranges (day>=1 && day<=5), comparing when equality was needed or vice versa.`},
		{"LogicBoolean", "specific", "Logic", `Tag for: if (x = true) (assignment instead of comparison), returning true/false in the wrong branch, unnecessary if (bool == true) revealing misunderstanding of boolean type, using 0/1 instead of true/false.`},
		{"StringFormat", "specific", "Strings", `Tag when the student cannot produce the expected output format even when their logic is close: wrong spacing, missing separators, wrong order of concatenated pieces in the final output string.`},
		{"StringConcat", "specific", "Strings", `Tag when concatenation is missing, in wrong order, or produces wrong result. Not about output format (that is StringFormat) — about the mechanical act of joining strings.`},
		{"StringIndex", "specific", "Strings", `Tag for wrong index, index out of bounds, off-by-one in string position, using wrong substring bounds.`},
		{"StringLen", "specific", "Strings", `Tag when the student confuses .length() method with .length property (Java arrays), or uses wrong length value for substring bounds, or does not account for zero-based indexing with length.`},
		{"StringEqual", "specific", "Strings", `Tag when the student uses == on strings instead of .equals(), or compares the wrong parts of strings. Do NOT tag for numeric comparisons — that is LogicCompareNum.`},
		{"CharEqual", "specific", "Strings", `Tag when comparison at the character level is wrong: comparing wrong char position, wrong char literal, confusing char with String type.`},
		{"ArrayIndex", "specific", "Arrays", `Tag for out-of-bounds access, off-by-one in array indexing, wrong index variable, confusing index with value stored at that index.`},
		{"DefFunction", "specific", "Functions", `Tag when the problem asks for a specific helper method and the student's helper is missing, incomplete, has wrong signature, or has broken logic inside it.`},
	}
}

func seedKCMetadata(db *sql.DB) {
	for i, s := range defaultKCSeeds() {
		// Row already exists (from ingest) most of the time — only backfill
		// category/gap_signal if still empty, and only set sort_order once.
		db.Exec(`INSERT OR IGNORE INTO kcs (name, kind, category, gap_signal, sort_order) VALUES (?, ?, ?, ?, ?)`,
			s.name, s.kind, s.category, s.gapSignal, i)
		db.Exec(`UPDATE kcs SET category = ? WHERE name = ? AND category = ''`, s.category, s.name)
		db.Exec(`UPDATE kcs SET gap_signal = ? WHERE name = ? AND gap_signal = ''`, s.gapSignal, s.name)
		db.Exec(`UPDATE kcs SET sort_order = ? WHERE name = ? AND sort_order = 0`, i, s.name)
	}
}

type promptComponentSeed struct {
	key     string
	label   string
	content string
}

// Placeholders substituted at render time: {{problem_id}} {{assignment_id}}
// {{requirement}} {{score}} {{kc_count}} {{structural_kcs}} {{required_kcs}}
func defaultPromptComponents() []promptComponentSeed {
	return []promptComponentSeed{
		{"preamble", "1. Preamble & problem context", `You are an expert CS1 instructor analyzing a single student Java code submission to identify knowledge gaps.

PROBLEM CONTEXT:
{
  "problem_id": {{problem_id}},
  "assignment_id": {{assignment_id}},
  "requirement": {{requirement}},
  "student_score": {{score}}
}`},
		{"kc_definitions_intro", "2. KC definitions intro", `KC DEFINITIONS:
Below are all {{kc_count}} Knowledge Components (KCs) used in this course. Each includes what a gap looks like in student code.`},
		{"kc_injection_template", "3. Required-KCs injection", `REQUIRED KCs FOR THIS PROBLEM: [{{required_kcs}}]
These are the KCs this problem is designed to test. Check these first. However, if the student's code reveals gaps in other KCs not on this list, tag those too.`},
		{"tagging_hierarchy", "4. Tagging hierarchy", `TAGGING HIERARCHY — CHECK SPECIFIC BEFORE STRUCTURAL:
KCs marked "structural" ({{structural_kcs}}) are tags of LAST RESORT.
Always check "specific" KCs first (Logic, Math, String, Array, Function).
If a specific KC explains the error, tag ONLY the specific KC. Do NOT also tag the structural KC.
Tag a structural KC only when the structure itself is the problem and no specific KC explains it.

Examples:
- Wrong condition inside an if-statement → LogicCompareNum or LogicBoolean, NOT If/Else
- Wrong loop boundary value → LogicCompareNum, NOT For
- Wrong arithmetic inside a loop body → Math+-*/, NOT For
- Student uses && where || needed inside an if → LogicAndNotOr, NOT If/Else`},
		{"redundancy_check", "5. Redundancy check", `REDUNDANCY CHECK — apply before finalizing your tags:
For every structural KC ({{structural_kcs}}) in your list, ask: "If I remove this tag, does my diagnosis lose any information?" If the answer is no — if a specific KC already explains the error — drop the structural tag.`},
		{"disambiguation_intro", "6. Disambiguation rules intro", `DISAMBIGUATION RULES:
When two KCs seem applicable, use these rules to pick the correct one.`},
		{"critical_rules", "7. Critical rules", `CRITICAL RULES:
1. If the code is a trivial placeholder (e.g., just "return true;" or "return 0;") with no real attempt, return empty knowledge_gaps.
2. If the student scored 1.0 (perfect), return empty knowledge_gaps.
3. Only use KC names from the {{kc_count}} defined above. Do not invent new names.
4. Think through your reasoning BEFORE listing gaps. Write your reasoning first, then decide on tags.`},
		{"output_format", "8. Output format", `OUTPUT FORMAT:
Respond with ONLY a JSON object, no other text:
{
  "reasoning": "Brief explanation of what the student did wrong and which KCs are affected, applying the hierarchy (specific before structural).",
  "knowledge_gaps": ["KC1", "KC2"]
}`},
		{"student_code_label", "9. Student code label", `STUDENT CODE:`},
	}
}

func seedPromptComponents(db *sql.DB) {
	for i, c := range defaultPromptComponents() {
		db.Exec(`INSERT OR IGNORE INTO prompt_components (key, label, content, sort_order) VALUES (?, ?, ?, ?)`,
			c.key, c.label, c.content, i)
	}
}

func defaultDisambiguationRules() []string {
	return []string{
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
}

func seedDisambiguationRules(db *sql.DB) {
	var count int
	db.QueryRow(`SELECT COUNT(*) FROM disambiguation_rules`).Scan(&count)
	if count > 0 {
		return
	}
	for i, rule := range defaultDisambiguationRules() {
		db.Exec(`INSERT INTO disambiguation_rules (rule, sort_order) VALUES (?, ?)`, rule, i)
	}
}
