# V3 (KCDP) Prompt — Full Specification

How the V3 knowledge-gap detection prompt is built, what goes into it, what does
**not**, and what happens to the model's output. Every claim here is traceable to
[`lib/v3_prompt.py`](lib/v3_prompt.py) (prompt assembly) and the run/parse loop in
[`experiments/ablation/exp21_v3_ablation.ipynb`](experiments/ablation/exp21_v3_ablation.ipynb)
(the same harness used for the V3 eval).

---

## 1. Unit of work

One prompt = **one Gemini call per (student, problem) submission**. The pipeline
iterates a student's submissions in problem-ID order and:

- **Skips perfect scores.** If `score >= 1.0`, the problem is annotated with an
  empty gap list and **no model call is made** (it is not "called and returned
  empty" — it is never sent).
- Otherwise it builds the prompt below and calls the model.

So "problems scored" and "problems called" differ: parse rates and call counts
are over the **non-perfect** submissions only.

Model: `gemini-2.5-flash`. Decoding: `temperature = 0.3`, and **nothing else is
set** — no top-p, top-k, max-tokens, stop sequences, or system instruction. The
call is `generate_content(model, contents=prompt_text, config=GenerateContentConfig(temperature=0.3))`.

---

## 2. Inputs and where they come from

| Field injected | Source | Notes |
|---|---|---|
| `problem_id` | `problem_prompts.csv` (`ProblemID`) | identifies the problem |
| `assignment_id` | `problem_prompts.csv` (`AssignmentID`) | maps to chapter/difficulty |
| `requirement` | `problem_prompts.csv` (`Requirement`) | **the problem statement** the student was asked to solve |
| `required_kcs` | `problem_prompts.csv` (18 binary KC columns == 1.0) | the KCs the problem is *designed* to test |
| `student_code` | `student_<sid>.json` (`submissions[pid].code`) | raw Java, injected verbatim |
| `score` | `student_<sid>.json` (`submissions[pid].score`) | 0.0–1.0 |

Everything else in the prompt (role line, the 18 KC definitions, tagging
hierarchy, redundancy worked-examples, disambiguation rules, critical rules,
output schema) is **static text** baked into `lib/v3_prompt.py` — identical on
every call.

---

## 3. Prompt anatomy (assembled order)

The prompt is a single text string assembled top-to-bottom in this order:

1. **Role declaration** — one line: *"You are an expert CS1 instructor analyzing
   a single student Java code submission to identify knowledge gaps."*

2. **PROBLEM CONTEXT** (JSON block) — `problem_id`, `assignment_id`,
   `requirement`, `student_score`. **This is where the problem statement enters
   the prompt** — as the `requirement` value, its own component, separate from
   the required-KC section and from the code.

3. **KC DEFINITIONS** (JSON block) — all **18** KCs, each with `category`
   (Control Flow / Loops / Math / Logic / Strings / Arrays / Functions),
   `type` (`structural` or `specific`), and a `gap_signal` describing what a gap
   in that KC looks like in code. Always all 18, regardless of the problem.

4. **KC injection block** — the per-problem KC list. Controlled by `kc_mode`:
   - `per_problem` (default): `REQUIRED KCs FOR THIS PROBLEM: [...]` followed by
     *"Check these first. However, if the student's code reveals gaps in other
     KCs not on this list, tag those too."* → the list is a **prior, not a
     constraint**; off-list tagging is explicitly permitted.
   - `full_vocab`: `AVAILABLE KCs: [all 18]` with no shortlist — decide purely
     from the code. (Used by the `no_kc` ablation.)

5. **TAGGING HIERARCHY** — "check specific before structural." Declares the five
   structural KCs (If/Else, NestedIf, While, For, NestedFor) as tags of last
   resort, with four inline examples.

6. **REDUNDANCY CHECK** — worked examples (If/Else, For, While, NestedIf,
   NestedFor) each showing a CORRECT vs WRONG tag set, plus a "When TO tag
   structural KCs" list. These examples express tags as bare KC names, e.g.
   `["LogicCompareNum"]`.

7. **DISAMBIGUATION RULES** (JSON block) — the 14 KC-vs-KC tie-breakers.
   **Ablatable** via `rules_mode`: `full` (14), `reduced` (4: indices
   `[0,1,2,12]`), or `none` (block omitted entirely).

8. **CRITICAL RULES** — see §6. Exactly **four** rules.

9. **OUTPUT FORMAT** — the JSON schema example (see §5).

10. **STUDENT CODE** — the raw submission inside a ```java fence.

---

## 4. The two ablation flags

`build_v3_prompt(..., rules_mode="full", kc_mode="per_problem")`. Defaults
reproduce the original V3 prompt byte-for-byte.

| Flag | Values | Effect |
|---|---|---|
| `rules_mode` | `full` / `reduced` / `none` | size of the DISAMBIGUATION RULES block (component 7) |
| `kc_mode` | `per_problem` / `full_vocab` | whether component 4 is a per-problem shortlist or the full 18-KC vocabulary |

No other component changes between conditions.

---

## 5. Output schema (V3) — and how it differs from V1/V2

**V3** asks for exactly two fields:

```json
{
  "reasoning": "Brief explanation ... applying the hierarchy (specific before structural).",
  "knowledge_gaps": ["KC1", "KC2"]
}
```

- `knowledge_gaps` is a **flat list of bare KC-tag strings**.
- `reasoning` is **one** free-text explanation for the whole response — **not**
  per tag.
- There is **no** `missing_concept`, `evidence`, `severity`, `gap`, or
  per-tag justification field in V3.

**V1/V2** ([`lib/prompts.py`](lib/prompts.py)) is the version that has those:
there `knowledge_gaps` is a list of **objects** —
`{ "gap": "...", "evidence": "...", "missing_concept": "STRICT_KC_TAG", "severity": "..." }`
— plus `future_predictions`, `recommended_intervention`, etc. If a draft
references `missing_concept` or a per-tag justification, it is describing
**V1/V2**, not V3.

---

## 6. The CRITICAL RULES (verbatim) — there are four, not five

```
CRITICAL RULES:
1. If the code is a trivial placeholder (e.g., just "return true;" or "return 0;")
   with no real attempt, return empty knowledge_gaps.
2. If the student scored 1.0 (perfect), return empty knowledge_gaps.
3. Only use KC names from the 18 defined above. Do not invent new names.
4. Think through your reasoning BEFORE listing gaps. Write your reasoning first,
   then decide on tags.
```

"Never tag a construct the student did not write" is **not** in this block — it
appears in **disambiguation rule 14** (NestedFor vs While) and in the structural
KC `gap_signal`s, not among the critical/behavioral rules.

---

## 7. What happens to the output (parse → clean → store)

1. **Fence stripping.** Leading ```` ```json ```` / ```` ``` ```` and a trailing
   ```` ``` ```` are removed, then the string is `.strip()`ed.
2. **JSON parse.** `json.loads` on the cleaned string (`status = "ok"`).
3. **Brace-extraction fallback.** If that fails, take the substring from the
   first `{` to the last `}` and retry (`status = "ok_extracted_json"`). This is
   the only structural "repair" — there is **no** trailing-comma fixing, quote
   normalization, or encoding repair.
4. **Hard fail.** If both fail, store `{"reasoning": raw_text, "knowledge_gaps": []}`
   with `status = "parse_error: ..."`. The problem ends up with **no gaps**; the
   call is **not retried**.
5. **Tag allow-list filter (`clean_gaps`).** Each returned gap is kept only if it
   is one of the 18 valid KCs. Invalid / invented tags are **dropped**, not
   repaired and not retried. (They are also recorded under `invalid_kcs` in the
   raw record for audit.)
6. **API errors** (exceptions on the call) are logged to the per-student
   `errors` list and the problem is stored with empty gaps. No retry.

Net behavior: **failed parses and invalid tags are logged and excluded, never
repaired or retried** (beyond the deterministic fence-strip + brace-extraction in
steps 1–3).

---

## 8. What is NOT in the prompt

- No few-shot *student-submission* examples — the only worked examples are the
  abstract redundancy/hierarchy cases (components 5–6).
- No chain-of-thought scaffold beyond "write reasoning first" (critical rule 4).
- No rubric, no test cases, no expected/reference solution, no compiler output.
- No conversation history — each call is independent and stateless.
- No severity, confidence, evidence, or intervention fields (those are V1/V2).
- No system instruction and no decoding controls other than `temperature=0.3`.
