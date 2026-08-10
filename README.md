# Kintsugi

Kintsugi detects knowledge gaps in introductory programming submissions using a large language model, without training or fine-tuning any model. It reads a student's Java code and returns the specific CS1 concepts the student failed to demonstrate, drawn from a fixed instructor-defined vocabulary. The name comes from the Japanese art of repairing broken pottery with gold, since the goal is to make invisible gaps visible so they can be repaired.

This repository is the research code and evaluation harness behind the M.S. thesis _LLM-Based Knowledge Component-Constrained Diagnostic Prompting for Automated Knowledge Gap Detection_ (defended July 2026).

## What it does

The core method is **KCDP** (Knowledge Component Diagnostic Prompting), a single prompt that constrains the model's output to a closed list of concepts. The model is shown the concept list for the course and the concepts a given problem tests, then asked, for each one, whether the student demonstrated it or missed it. Output that names any concept outside the list is discarded. No student history, no fine-tuning, no model training. Every constraint lives in the prompt.

The central finding is **constraint beats context**. The closed concept list is what drives agreement with human experts. Adding student history or richer scaffolding did not help.

## Headline results

Evaluated on 372 common annotations across 10 struggling students, scored against two human raters, with human-human agreement as the ceiling. Primary model is Gemini 2.5 Flash (`gemini-2.5-flash`, temperature 0.3).

| Metric     | Human ceiling | KCDP (V3) | % of ceiling |
| ---------- | ------------- | --------- | ------------ |
| Problem F1 | 0.885         | 0.839     | 94.8%        |
| Cohen's κ  | 0.669         | 0.557     | 83.2%        |
| Gwet AC1   | 0.963         | 0.953     | 98.9%        |

**Ablation (Gemini 2.5 Flash), showing constraint beats context.** Removing the concept constraint is what breaks the method. Removing the disambiguation rules does not hurt, and is the recommended deployment variant.

| Condition                          | F1    | κ     |
| ---------------------------------- | ----- | ----- |
| No rules (concept constraint kept) | 0.847 | 0.571 |
| Baseline (constraint + full rules) | 0.831 | 0.548 |
| No concept constraint              | 0.820 | 0.496 |

**Cross-model replication.** The same prompt transferred to DeepSeek-V3 (`deepseek-chat`, temperature 0.3) without modification, reaching F1 = 0.825, κ = 0.535.

Full sourced numbers, with the on-disk file behind every value, are in [`results_consolidated/THESIS_RESULTS.md`](results_consolidated/THESIS_RESULTS.md).

## The prompt arc

The method was reached in three steps, each answering a question the previous one raised.

- **V1, curriculum-aware prompting.** The model is told the course curriculum but given no per-problem constraint.
- **V2, context-enriched prompting.** V1 plus difficulty weighting and richer context.
- **V3, KCDP.** The model's output is constrained to the concepts a problem actually tests. This is the headline method.

The prompt is specified in full in [`docs/v3_prompt_spec.md`](docs/v3_prompt_spec.md) and [`docs/PROMPTS.md`](docs/PROMPTS.md).

## Setup

Python 3.14.

```bash
pip install -r requirements.txt
```

LLM access needs API keys in a `.env` file. Gemini is the primary model. DeepSeek is used for cross-model validation and for the dashboard's live diagnosis.

```
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=...
```

## Experiment workflow

Experiments run as ordered notebooks under `experiments/`, grouped by phase.

- `phase1_prompt_selection` — choosing the prompt strategy to carry forward.
- `phase2_mental_model` — student-history injection, the approach that did not improve agreement.
- `phase3_validation` — validation runs.
- `phase4_knowledge_tracing` — Q-matrix and knowledge-tracing comparison work.
- `phase5_human_validation` — the human-rater evaluation behind the headline numbers.
- `ablation` — the V3 ablation, including the DeepSeek cross-model run.

Shared logic lives in `lib/`, including prompt assembly (`v3_prompt.py`, `prompts.py`), output normalization (`normalizer.py`), and the prediction validator (`prediction_validator.py`).

## Instructor dashboard

`dashboard/` is a proof-of-concept triage tool that turns KCDP annotations into a class concept map, an at-risk student list, and a per-student drill-down with live diagnosis. Frontend is React, TypeScript, and Tailwind. Backend is Go with an embedded SQLite database. Live diagnosis calls DeepSeek-V3.

```bash
cd dashboard
python ingest/ingest.py          # build kintsugi.db (run once)

cd backend
go mod tidy && go build -o backend .
DB_PATH=../kintsugi.db ./backend # serves on :8080

cd ../frontend
npm install && npm run dev       # serves on :5173
```

Setup details and the ranking formula are in [`dashboard/README.md`](dashboard/README.md).

## Build a Gap Finder for your own course

KCDP splits into a fixed part (the prompt and output checking) and a course-specific part (a concept list and a problem-to-concept map). A new instructor builds a working gap finder by filling in only the second part. The step-by-step template is in [`GAP_FINDER_TEMPLATE.md`](GAP_FINDER_TEMPLATE.md).

This is validated for CS1-style programming courses. The template mechanism is general, but the empirical results are for programming and should not be assumed to carry to other subjects without testing.

## Repository layout

| Path                    | Contents                                          |
| ----------------------- | ------------------------------------------------- |
| `experiments/`          | Ordered notebooks, grouped by phase               |
| `lib/`                  | Shared prompt, normalization, and validation code |
| `dashboard/`            | Instructor triage dashboard (Go + React + SQLite) |
| `dataset/`              | CodeWorkout CS1 data, rater KC tags, topics       |
| `docs/`                 | Prompt specs, ablation results, report            |
| `results/`              | Raw per-experiment outputs                        |
| `results_consolidated/` | One-file sourced results reference                |
| `human_validation/`     | Human rater sheet and analysis                    |

## Dataset

CodeWorkout CS1 Java submissions, annotated against 18 knowledge components selected from the CSEDM Data Challenge tag set (If/Else, NestedIf, While, For, NestedFor, the Math and Logic families, the String and Char families, ArrayIndex, and DefFunction).

## Citation

If you use this work, please cite the thesis. Pranay Ghuge, _LLM-Based Knowledge Component-Constrained Diagnostic Prompting for Automated Knowledge Gap Detection_, M.S. thesis, University of Massachusetts Dartmouth, 2026.
