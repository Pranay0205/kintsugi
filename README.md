# Kintsugi

Kintsugi (named after the Japanese art of repairing broken pottery with gold) is a research prototype designed to analyze student programming submissions and illuminate invisible gaps in cybersecurity awareness. By leveraging Large Language Models (LLMs) and Knowledge Tracing (KT), it distinguishes between fundamental coding errors ("Skill Gaps") and overlooked security principles ("Awareness Gaps") to inform more resilient curriculum design.

## Notebook Workflow

The project now uses three focused notebooks instead of one monolithic flow:

- `single_student_experiments.ipynb`  
  Single-student prompt strategy experiments (Experiments 1-4).
- `single_student_mental_model_injection.ipynb`  
  Single-student mental-model construction and context-enriched prompt evaluation.
- `batch_prompt_experiments.ipynb`  
  Cohort-level prompt strategy experiments and summary metrics.

`student_assessment_analysis.ipynb` is preserved as the original notebook and is intentionally left intact.

## Shared Library Structure

Common notebook logic is centralized in `lib/`:

- `lib/experiment_utils.py`
  - Data loading and student/cohort selection
  - Prompt strategy registry
  - Submission-level analysis runner
  - Strategy summary and CSV export helpers

- `lib/mental_model.py`
  - Skill map/profile construction
  - Prerequisite graph and weak-skill extraction
  - Mental-model payload builder
  - Context-enriched prompt evaluation helpers

Existing modules (`lib/llm_batch_analyzer.py`, `lib/prompts.py`, `lib/normalizer.py`, `lib/prediction_validator.py`) remain supported for CLI and thesis analysis flows.

## Recommended Run Order

1. Run all cells in `single_student_experiments.ipynb`
2. Run all cells in `single_student_mental_model_injection.ipynb`
3. Run all cells in `batch_prompt_experiments.ipynb`

Each notebook writes CSV outputs for downstream reporting.

## Runtime Entry Points

The legacy CLI flow has been removed.

- Preferred workflow: run the project through the notebook workflows listed above.
- CLI files (`cli.py`, `commands/`) were intentionally retired to reduce maintenance overhead and avoid duplicated execution paths.

## Legacy Notebook Policy

Some exploratory notebooks are archived under `archive/legacy_notebooks/`.

- These runs are retained for reproducibility and audit trail.
- They are not used for final thesis claims when evaluation setup is found to be biased or unrealistic.
- Example: `archive/legacy_notebooks/thesis_analysis_unrealistic_metrics.ipynb` is treated as a pilot run with invalidly optimistic metrics and excluded from final reported results.
