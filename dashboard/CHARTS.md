# Dashboard Charts — Instructor Reading Guide

Each chart on the Class Skill Map page answers a different teaching question.
Read them in order: overview → what to reteach → who needs help → which problems to fix.

---

## Reteach Before Moving On (action cards)

**What it shows:** KCs flagged by 70%+ of the class (≥7 of 10 students).

**How to read it:** If a KC appears here, the majority of the class has not yet mastered it.
Covering the next topic before fixing this one compounds the problem — students will carry
the gap forward into harder problems that build on this KC.

**What to do:** Before the next lecture, run a targeted 10–15 min re-teach on these KCs.
Use the Student × KC Matrix below to see which students need individual follow-up.

---

## 1. Gap Frequency by KC (horizontal bar chart)

**What it shows:** Total number of times each KC was flagged across all submissions,
sorted high to low. Color bands mark severity tiers (high / medium / low / rare).

**How to read it:** A long bar means many submissions had that KC flagged — not necessarily
that many *students* have that gap. A student who struggles with `LogicAndNotOr` across
10 problems inflates this count. Compare with the Matrix to distinguish "one student,
many times" from "many students, once each."

**What to do:** High bars for specific KCs (Logic, Math, Strings) → targeted re-teach.
High bars for structural KCs (If/Else, For, While) → check whether the gap is really
a logic gap being over-labelled — the structural KCs are tags of last resort.

---

## 2. Gap Distribution by Category (treemap)

**What it shows:** Each tile represents one KC. Tile area is proportional to its total
gap count. Color groups KCs by category (Logic, Strings, Loops, etc.).

**How to read it:** A dominant color family means that whole KC category is struggling.
A large Logic block, for example, suggests students need help with conditional reasoning
broadly — not just one specific KC.

**What to do:** If one color dominates, plan a concept-level session on that category
rather than drilling individual KCs in isolation. E.g., a big orange (Logic) block →
dedicate a lab to compound boolean expressions before moving to the next assignment.

---

## 3. Gap Persistence (horizontal bar chart)

**What it shows:** For each KC, the percentage of students who had that KC flagged in the
**first half** of their problem sequence and still had it flagged in the **second half**.

- **Rose (≥70%):** Students are not self-correcting this gap. It persists across the course.
- **Orange (40–70%):** Partial self-correction. Some students are improving, others are not.
- **Emerald (<40%):** Most students naturally corrected this gap through practice alone.

**How to read it:** This is the most actionable single chart for planning next week's lesson.
A KC with high persistence means more practice problems are *not* working — you need
explicit re-teaching with explanation and worked examples.

A KC with low persistence (emerald) is self-correcting: students figure it out through
repetition. You can leave those to practice sets.

**What to do:** Prioritize high-persistence KCs for the next lecture slot. Low-persistence
KCs only need extra practice problems assigned.

---

## 4. Hardest Problems (bar chart)

**What it shows:** The top 20 problems ranked by how many students had at least one gap
flagged on that problem. The Y-axis is "number of students flagged."

**How to read it:** A tall bar means many students struggled on that specific problem.
This could be because:
- The problem tests a genuinely hard KC
- The problem's wording is ambiguous
- The problem is positioned too early in the sequence (prerequisite not yet taught)

**What to do:**
- Problems flagging 8–10 students → add a worked example or hint in the problem statement.
- Problems clustering at the top that test the same KC → that KC may need pre-teaching
  before students attempt the problem set.
- Consistently hard problems across multiple assignments → consider restructuring problem order.

---

## 5. Student × KC Gap Matrix (heatmap grid)

**What it shows:** A grid where each row is a student and each column is a KC.
Cell color intensity encodes gap count — darker = flagged more often.
Color hue encodes KC category (same palette as the treemap).

**How to read it:**

- **Dark column** → class-wide gap. Most students struggle with this KC. Plan a re-teach.
- **Dark row** → one student has broad, persistent gaps across many KCs. Needs individual
  attention or a one-on-one session. Combine with the At-Risk Triage ranking.
- **Isolated dark cell** → one student, one KC. Assign targeted practice or a check-in
  question for that student on that topic.
- **Empty cell** → the student either aced every problem testing that KC (score = 1.0 skips
  flagging) or the problem set did not cover that KC for them.

**What to do:** Use this matrix alongside the Triage list. Students at the top of the
Triage list should have the darkest rows here. If a student's triage rank is high but
their row looks light, check whether their rank is driven by a single high-recurrence KC
rather than broad weakness.

---

## Interpreting gaps together

| Signal | Likely cause | Action |
|---|---|---|
| Many dark columns + high persistence | Conceptual gaps across the class | Re-teach whole KC families, not just drill |
| Few dark columns, one dark row | One student is an outlier | 1:1 session; others may not need intervention |
| Hard problems cluster on same KCs | KC introduced too early | Move KC re-teach before that problem set |
| Low persistence + high frequency bar | Students self-correct; just need reps | Assign more practice, no re-teach needed |

---

*Gap flags are produced by the KCDP V3 diagnostic prompt. Structural KCs (If/Else, NestedIf,
While, For, NestedFor) are tags of last resort — a specific KC (Logic, Math, Strings)
explains most errors, so structural flags should be rare and treated cautiously.*
