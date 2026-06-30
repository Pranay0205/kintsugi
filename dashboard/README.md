# KCDP Instructor Dashboard

Proof-of-concept triage tool (thesis contribution 3). Turns DeepSeek V3 KCDP annotations into a class skill map, at-risk triage list, and per-student drill-down with live diagnosis.

## Setup

### 1. Ingest (run once)

```bash
cd dashboard
python ingest/ingest.py
# Produces kintsugi.db (~200 KB)
```

### 2. Backend

```bash
cd dashboard/backend
# First time only:
go mod tidy
go build -o backend.exe .

# Run:
DB_PATH=../kintsugi.db ./backend.exe
# Or on Windows:
$env:DB_PATH="../kintsugi.db"; .\backend.exe
```

Optional env vars:
- `DB_PATH` — path to SQLite file (default: `../kintsugi.db`)
- `DEEPSEEK_API_KEY` — required for live diagnosis (POST /api/diagnose)
- `PORT` — HTTP port (default: 8080)

### 3. Frontend

```bash
cd dashboard/frontend
npm install
npm run dev      # dev mode with proxy to :8080
# or:
npm run build    # static build in dist/
```

Open http://localhost:5173

## Data

| Table | Source | Notes |
|---|---|---|
| kcs | problem_prompts.csv | 18 KCs, kind=specific/structural |
| students | DeepSeek ablation files | 10 struggling students |
| submissions | annotation_inputs/student_*.json | code + score per problem |
| submission_gaps | llm_ablation_deepseek_baseline_*.json | gap tags, no reasoning |
| recurrence | exp16_predictions_30students.csv | Gemini-estimated (κ 0.535 ≈ DeepSeek 0.548) |

**Frozen study records** (`source=study`): DeepSeek V3 gap tags, reasoning not captured.  
**Live records** (`source=live`): Full reasoning + gaps from DeepSeek API, do not fold into validated triage scores.

## Ranking formula

```
rank_score = Σ over flagged KCs of (gap_count(student, kc) × recurrence_hit_rate(kc, cluster))
```

`sub100_count` is shown as the confidence cue; not folded into the score.

## Validated anchor

Flagged gaps recurred as next-problem failure 77.0% of the time (148 predictions) for struggling students vs 26.4% baseline (Section 5.5 / exp16).
