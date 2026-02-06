# Kintsugi Project - AI Assistant Context

You are assisting with the **Kintsugi** project — a Master's thesis research tool that uses LLM prompt engineering to detect knowledge gaps in student code submissions and generate actionable curriculum insights for instructors.

---

## PROJECT GOAL

Build a **transferable, LLM-based pipeline** that:

1. Takes a class worth of student code submissions (e.g., assignments 1-5)
2. Analyzes them using prompt engineering (NOT ML models)
3. Produces a **class-level instructor report**: top gaps, % affected, at-risk students, curriculum recommendations
4. Works on **CS1 (Java)** first, then transfers to **Cybersecurity** courses with minimal changes

The thesis contribution is: **"A domain-transferable knowledge gap detection framework using prompt engineering — demonstrated on CS1 and applied to cybersecurity education without retraining."**

---

## DATASET: CodeWorkout (CSEDM Data Challenge)

### Files

```
dataset/CodeWorkout/
├── MainTable.csv          # 201,570 rows - Event logs
├── LinkTables/
│   ├── CodeStates.csv     # 69,627 rows - Actual student code
│   └── Subject.csv        # 381 rows - Student grades
└── Problem_Prompts/
    └── problem_prompts.csv # KC matrix per problem
```

### Schema

**MainTable.csv** — One row per EVENT (not per submission):
| Column | Description |
|--------|-------------|
| SubjectID | Student identifier |
| ProblemID | Problem identifier (50 unique problems) |
| Attempt | Attempt number per student-problem |
| CodeStateID | Links to actual code in CodeStates.csv |
| EventType | `Run.Program`, `Compile`, `Compile.Error` |
| Score | 0.0-1.0 ratio of test cases passed (only on Run.Program events) |
| Compile.Result | `Success` or `Error` |
| AssignmentID | Assignment grouping |
| ServerTimestamp | When the event occurred |

**CodeStates.csv**: CodeStateID → Code (actual Java source)  
**Subject.csv**: SubjectID → X-Grade (final course grade 0.0-1.0)

### Key Data Facts

- **372 unique students**, **50 unique problems**, **191,584 joined rows**
- One code submission generates **multiple event rows** (Run.Program + Compile + Compile.Error)
- Score of 0.0 = no tests passed; 1.0 = all passed

---

## PROJECT STRUCTURE

```
kintsugi/
├── utils/
│   ├── __init__.py
│   ├── constants.py        # Paths, API keys, thresholds
│   └── dataset.py          # Data loading: load_data(), load_joined_datasets(), get_best_attempts()
├── lib/
│   ├── __init__.py
│   ├── prompts.py           # All 4 prompt strategies (Zero-Shot, Few-Shot, CoT, Curriculum-Aware)
│   ├── normalizer.py        # Canonical gap tag normalization (10 tags + regex patterns)
│   ├── llm_batch_analyzer.py  # Gemini API calls, response parsing, pipeline orchestration
│   └── prediction_validator.py # Validates predictions against future performance, P/R/F1 metrics
├── commands/
│   ├── __init__.py
│   ├── analyze.py           # CLI: batch analysis command
│   └── validate.py          # CLI: mixed-sample validation command
├── cli.py                   # Argparse entry point
├── thesis_analysis.ipynb    # Main notebook: 4-strategy comparison with P/R/F1
├── codeworkout_analysis.ipynb  # EDA notebook
├── classroom_analysis.ipynb    # Class-level batch analysis
└── pyproject.toml
```

### Module Responsibilities

| Module                        | Purpose                                                                                              |
| ----------------------------- | ---------------------------------------------------------------------------------------------------- |
| `lib/prompts.py`              | Defines 4 prompt functions + `SIMPLE_STRATEGIES` registry                                            |
| `lib/normalizer.py`           | `normalize_gap_tag()`, `normalize_predictions()`, `map_prediction_to_topic_columns()`                |
| `lib/llm_batch_analyzer.py`   | `format_submissions()`, `clean_json_response()`, `analyze_student_submissions()`, `run_analysis()`   |
| `lib/prediction_validator.py` | `validate_predictions()`, `compute_binary_metrics()`, `compute_metrics_by_strategy()`                |
| `utils/dataset.py`            | `load_joined_datasets()`, `get_best_attempts()`, `load_topics_json()`, `load_problem_descriptions()` |
| `utils/constants.py`          | All paths, `FOCUS_PROBLEMS`, `VALIDATION_PROBLEMS`, thresholds                                       |

---

## KNOWLEDGE COMPONENT (KC) TAXONOMY

From `problem_prompts.csv` — each problem maps to required concepts:

- **If/Else, NestedIf** — Conditionals
- **While, For, NestedFor** — Loops
- **Math+-\*/, Math%** — Arithmetic
- **LogicAndNotOr, LogicCompareNum, LogicBoolean** — Logic
- **StringFormat, StringConcat, StringIndex, StringLen, StringEqual, CharEqual** — Strings
- **ArrayIndex** — Arrays
- **DefFunction** — Functions

### Canonical Tags (10)

Used for cross-strategy normalization in `lib/normalizer.py`:  
Loop, NestedLoop, String, Array, Logic, Condition, Method, Math, Indexing, Comparison

---

## LLM CONFIGURATION

- **Model**: Gemini 2.5 Flash (via `google.genai`)
- **Temperature**: 0.3 (low for consistency)
- **Response format**: `application/json`
- **API Key**: `.env` → `GEMINI_API_KEY`

---

## PROMPT STRATEGIES (Thesis Comparison)

### 1. Zero-Shot

Direct instruction, no examples. Returns `{knowledge_gaps, future_predictions}`.

### 2. Few-Shot

Instruction + 2 annotated examples of gap identification.

### 3. Chain-of-Thought

4-step reasoning chain: (1) What does the code do? (2) Where does it fail? (3) What concept is missing? (4) Predict future impact.

### 4. Curriculum-Aware (Hybrid)

Role-based + curriculum context + few-shot examples + strict KC tags.  
Uses `build_curriculum_aware_prompt(topics, problems, focus_ids)` from `lib/prompts.py`.

---

## VALIDATION METHODOLOGY

### Mixed Sampling

- 15 persistent strugglers (low early + low future scores)
- 15 confirmed non-struggling (high early + high future scores)
- Focus problems: [32, 33, 34] (early signal)
- Validation problems: [36, 37, 38, 39, 40] (ground truth)

### Binary Classification

- **predicted_struggle**: True when >= 50% of verifiable LLM predictions are confirmed by low future scores
- **actual_struggle**: Ground-truth label from mixed sampling
- Metrics: TP, FP, FN, TN → Precision, Recall, F1, Accuracy per strategy

---

## CODING CONVENTIONS

- Python 3.14, pandas, matplotlib
- Jupyter notebooks for analysis, `.py` files for reusable modules
- Package manager: `uv`
- Virtual env: `kintsugi`
- No module-level side effects (data loading is lazy/on-demand)
- All prompts in `lib/prompts.py`, all normalization in `lib/normalizer.py`

---

## WHAT TO PRIORITIZE

1. **Prompt strategy comparison** (thesis contribution)
2. **Validation with real metrics** (P/R/F1 on mixed sample)
3. **Clean, thesis-ready output** (tables, charts, exportable CSV)
4. **Modular and transferable code** (will reuse for cybersecurity phase)

Do NOT:

- Build ML models (the point is prompt engineering without training)
- Over-engineer predictions (diagnosis + correlation, not a prediction system)
- Suggest complex architectures (data → LLM → report)
- Ignore the cybersecurity transfer goal (everything should be domain-swappable)
