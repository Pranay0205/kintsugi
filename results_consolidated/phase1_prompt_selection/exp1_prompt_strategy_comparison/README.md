# Exp 1 — Prompt Strategy Comparison

- **Date:** 2026-03-02
- **Phase:** 1 (Prompt selection) · pre-V1
- **Notebook:** [experiments/phase1_prompt_selection/exp1_prompt_strategy_comparison.ipynb](../../../experiments/phase1_prompt_selection/exp1_prompt_strategy_comparison.ipynb)
- **Status:** ✓ Healthy as a smoke test. Curriculum-Aware adopted as the baseline going into Phase 2.

## Question
Which of 4 prompt strategies — Zero-Shot, Few-Shot, Chain-of-Thought, Curriculum-Aware — is best suited for KC gap detection?

## Method
- 1 student (ID 14355, avg score 0.17, 5 submissions)
- Each prompt run on the same submissions
- Metrics computed: JSON-validity coverage and average latency only (no accuracy/F1)

## Key result
- All 4 strategies returned valid JSON on 5/5 submissions (100% coverage).
- Latency: Few-Shot 8.4s · Zero-Shot 10.7s · CoT 12.8s · Curriculum-Aware 14.7s.
- **Caveat:** no quality comparison was done. Curriculum-Aware was carried forward as the baseline based on structure alone, not measured accuracy.

## Files
- `single_student_14355_exp3_results.csv` — per-submission outputs across the 4 strategies
- `single_student_14355_exp4_summary.csv` — coverage and latency summary
