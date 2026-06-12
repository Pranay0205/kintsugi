"""Paired bootstrap significance test for the V3 (KCDP) prompt ablation.

Local re-analysis only — NO model calls. Reuses the stored per-problem
predictions from the ablation runs and the metric functions in `utils.metrics`
(problem_f1, compute_kappa, compute_gwet_ac1); the metric math is not
reimplemented here.

For each metric (Problem_F1, Cohen's kappa, Gwet's AC1) we report, per condition
vs the baseline, the observed delta, its 95% percentile bootstrap CI, and a
two-sided p (the fraction of replicates whose delta sign flips relative to the
observed delta). The AvgHuman view (mean of HA-vs-pred and HB-vs-pred) is used
throughout, matching `evaluate_llm_vs_humans`. The human-human ceiling is
bootstrapped for reference.

Outputs:
  - ablation_bootstrap_results.csv  (one row per metric per level + per delta)
  - a printed summary table
"""

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path("/mnt/d/Projects/kintsugi")
sys.path.insert(0, str(ROOT))

from utils.metrics import (
    problem_f1, compute_kappa, compute_gwet_ac1,
    evaluate_llm_vs_humans, KC_COLUMNS,
)

# --- Config -------------------------------------------------------------------
SEED = 20240611
B = 10_000
STUDENT_IDS = [10155, 9948, 14189, 14352, 14362, 14363, 14374, 14414, 14474, 14499]
CONDITIONS = ["baseline", "no_rules", "reduced", "no_kc"]
BASELINE = "baseline"

HUMAN_DIR = ROOT / "dataset" / "Rater_KC_Tags" / "Rated_KC_V3"
LLM_DIR = ROOT / "results" / "human_validation" / "ablation"
OUT_CSV = ROOT / "ablation_bootstrap_results.csv"

VALID_KCS = set(KC_COLUMNS)


# --- Loaders (verbatim conventions from exp21_v3_ablation.ipynb) --------------
def find_one(pattern, directory):
    matches = sorted(directory.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No file matched {pattern} in {directory}")
    return matches[-1]


def normalize_gaps(value):
    if isinstance(value, dict):
        gaps = value.get("gaps", [])
    elif isinstance(value, list):
        gaps = value
    else:
        gaps = []
    if not isinstance(gaps, list):
        return set()
    return {g for g in gaps if g in VALID_KCS}


def load_annotation_file(path):
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    sid = str(data.get("studentId", data.get("student_id", "unknown")))
    return sid, {f"{sid}_{pid}": normalize_gaps(v) for pid, v in data.get("annotations", {}).items()}


def merge_files(file_map):
    merged = {}
    for expected_sid, path in file_map.items():
        loaded_sid, anns = load_annotation_file(path)
        if loaded_sid != expected_sid:
            raise ValueError(f"Expected {expected_sid}, found {loaded_sid} in {path.name}")
        merged.update(anns)
    return merged


def load_condition(condition):
    return merge_files({str(sid): LLM_DIR / f"llm_ablation_{condition}_{sid}.json" for sid in STUDENT_IDS})


human_a = merge_files({str(sid): find_one(f"kc_annotations_Pranay Ghuge_{sid}_*.json", HUMAN_DIR) for sid in STUDENT_IDS})
human_b = merge_files({str(sid): find_one(f"kc_annotations_Arundhati Das_{sid}_*.json", HUMAN_DIR) for sid in STUDENT_IDS})
preds = {cond: load_condition(cond) for cond in CONDITIONS}


def common_items():
    """Common set: human_a ∩ human_b ∩ baseline LLM run (same as the V3 eval)."""
    return sorted(set(human_a) & set(human_b) & set(preds[BASELINE]),
                  key=lambda x: (int(x.split("_")[0]), int(x.split("_")[1])))


common = common_items()
N = len(common)


# --- Sanity: every condition scored on exactly the same pids ------------------
print(f"Common problem annotations: {N}")
print("Per-condition coverage of the common set:")
ok = True
for cond in CONDITIONS:
    have = set(preds[cond])
    missing = [k for k in common if k not in have]
    n_scored = len(have & set(common))
    flag = "OK" if (n_scored == N and not missing) else "MISMATCH"
    if flag != "OK":
        ok = False
    print(f"  {cond:>9}: {n_scored}/{N} common pids present  [{flag}]")
for name, rater in [("human_a", human_a), ("human_b", human_b)]:
    n_scored = len(set(rater) & set(common))
    flag = "OK" if n_scored == N else "MISMATCH"
    if flag != "OK":
        ok = False
    print(f"  {name:>9}: {n_scored}/{N} common pids present  [{flag}]")
if not ok:
    raise SystemExit("FAIL: conditions are not scored on an identical 372-pid set. Aborting.")
assert N == 372, f"Expected 372 common pids, got {N}"


# --- Precompute per-pid structures per (rater, pred) pair ----------------------
# F1 is a per-problem mean, so we precompute problem_f1 once per pid and average
# over the resample. kappa / AC1 are not decomposable per problem, so we keep the
# per-pid 18-cell binary blocks and recompute on each resampled vector.
def binary_block(anns):
    """(N, 18) int array: row per pid, 1 if KC present in that pid's gap set."""
    return np.array([[1 if kc in anns.get(pid, set()) else 0 for kc in KC_COLUMNS]
                     for pid in common], dtype=np.int8)


def pair_struct(rater, pred):
    f1 = np.array([problem_f1(rater.get(pid, set()), pred.get(pid, set())) for pid in common])
    return {"f1": f1, "X": binary_block(rater), "Y": binary_block(pred)}

# Pairs needed: HA-vs-cond and HB-vs-cond for the AvgHuman view, plus HA-vs-HB ceiling.
pairs = {}
for cond in CONDITIONS:
    pairs[("A", cond)] = pair_struct(human_a, preds[cond])
    pairs[("B", cond)] = pair_struct(human_b, preds[cond])
pairs[("A", "B")] = pair_struct(human_a, human_b)


def pair_metrics(key, idx):
    """(F1, kappa, AC1) for one (rater, pred) pair on a resample index array."""
    s = pairs[key]
    f1 = float(s["f1"][idx].mean())
    bx = s["X"][idx].reshape(-1).tolist()
    by = s["Y"][idx].reshape(-1).tolist()
    kappa = compute_kappa(bx, by)
    ac1 = compute_gwet_ac1(bx, by)["ac1"]
    return f1, kappa, ac1


def avg_human(cond, idx):
    """AvgHuman view for a condition: mean of HA-vs-cond and HB-vs-cond."""
    fa, ka, aa = pair_metrics(("A", cond), idx)
    fb, kb, ab = pair_metrics(("B", cond), idx)
    return ((fa + fb) / 2, (ka + kb) / 2, (aa + ab) / 2)


# --- Observed point estimates (full sample) -----------------------------------
full_idx = np.arange(N)
obs = {cond: dict(zip(("Problem_F1", "Cohen_kappa", "Gwet_AC1"), avg_human(cond, full_idx)))
       for cond in CONDITIONS}
ceil_f1, ceil_k, ceil_a = pair_metrics(("A", "B"), full_idx)
obs["ceiling"] = {"Problem_F1": ceil_f1, "Cohen_kappa": ceil_k, "Gwet_AC1": ceil_a}

# Cross-check the baseline against the known V3 table via the existing scorer.
avg_row = evaluate_llm_vs_humans(human_a, human_b, preds[BASELINE], common, KC_COLUMNS)[3]
print("\nBaseline point estimates (AvgHuman):")
print(f"  Problem_F1 = {obs['baseline']['Problem_F1']:.3f}  (scorer: {avg_row['Problem_F1']:.3f}, table: 0.831)")
print(f"  Cohen_kappa = {obs['baseline']['Cohen_kappa']:.3f}  (scorer: {avg_row['Cohen_kappa']:.3f}, table: 0.548)")
print(f"  Gwet_AC1   = {obs['baseline']['Gwet_AC1']:.3f}  (scorer: {avg_row['Gwet_AC1']:.3f}, table: 0.953)")
assert abs(obs["baseline"]["Problem_F1"] - 0.831) < 0.002, "baseline F1 does not match the table"
assert abs(obs["baseline"]["Cohen_kappa"] - 0.548) < 0.002, "baseline kappa does not match the table"
print("  Baseline matches the known table. Proceeding to bootstrap.\n")


# --- Paired bootstrap ---------------------------------------------------------
METRICS = ["Problem_F1", "Cohen_kappa", "Gwet_AC1"]
SERIES = CONDITIONS + ["ceiling"]
# boot[metric][series] -> array of B replicate values
boot = {m: {s: np.empty(B) for s in SERIES} for m in METRICS}

rng = np.random.default_rng(SEED)
print(f"Bootstrap: B={B}, seed={SEED}. Resampling {N} pids with replacement (paired).")
t0 = time.time()
for b in range(B):
    idx = rng.integers(0, N, N)  # shared across all conditions in this replicate
    for cond in CONDITIONS:
        f1, k, a = avg_human(cond, idx)
        boot["Problem_F1"][cond][b] = f1
        boot["Cohen_kappa"][cond][b] = k
        boot["Gwet_AC1"][cond][b] = a
    f1, k, a = pair_metrics(("A", "B"), idx)
    boot["Problem_F1"]["ceiling"][b] = f1
    boot["Cohen_kappa"]["ceiling"][b] = k
    boot["Gwet_AC1"]["ceiling"][b] = a
    if (b + 1) % 1000 == 0:
        el = time.time() - t0
        print(f"  {b+1:>6}/{B}  ({el:.0f}s, ETA {el/(b+1)*(B-b-1):.0f}s)")
print(f"Done in {time.time()-t0:.0f}s.\n")


# --- Summarize ----------------------------------------------------------------
def ci(arr):
    lo, hi = np.percentile(arr, [2.5, 97.5])
    return float(lo), float(hi)


rows = []
for m in METRICS:
    # Absolute levels (each condition + ceiling) with bootstrap CIs.
    for s in SERIES:
        lo, hi = ci(boot[m][s])
        rows.append({
            "metric": m, "type": "level", "label": s,
            "value": round(obs[s][m], 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4),
            "p_two_sided": "",
        })
    # Deltas vs baseline (paired per replicate).
    base_obs = obs[BASELINE][m]
    base_boot = boot[m][BASELINE]
    for cond in CONDITIONS:
        if cond == BASELINE:
            continue
        d_obs = obs[cond][m] - base_obs
        d_boot = boot[m][cond] - base_boot  # paired difference per replicate
        lo, hi = ci(d_boot)
        # two-sided p = fraction of replicates whose delta sign flips vs observed.
        p = float(np.mean(np.sign(d_boot) != np.sign(d_obs)))
        rows.append({
            "metric": m, "type": "delta", "label": f"{cond} - baseline",
            "value": round(d_obs, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4),
            "p_two_sided": round(p, 4),
        })

with OUT_CSV.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["metric", "type", "label", "value", "ci_low", "ci_high", "p_two_sided"])
    w.writeheader()
    w.writerows(rows)

# --- Printed summary ----------------------------------------------------------
print("=" * 78)
print(f"V3 ABLATION — PAIRED BOOTSTRAP (B={B}, seed={SEED}, N={N} pids)")
print("p_two_sided = fraction of replicates whose delta sign flips vs the observed delta.")
print("=" * 78)
for m in METRICS:
    print(f"\n## {m}")
    print(f"  {'level':<22} {'value':>7}   95% CI")
    for s in SERIES:
        r = next(x for x in rows if x["metric"] == m and x["type"] == "level" and x["label"] == s)
        print(f"  {s:<22} {r['value']:>7.3f}   [{r['ci_low']:.3f}, {r['ci_high']:.3f}]")
    print(f"  {'delta vs baseline':<22} {'delta':>7}   95% CI{'':>12}   p")
    for cond in CONDITIONS:
        if cond == BASELINE:
            continue
        r = next(x for x in rows if x["metric"] == m and x["type"] == "delta" and x["label"].startswith(cond))
        sig = "*" if (r["ci_low"] > 0 or r["ci_high"] < 0) else " "
        print(f"  {cond+' - baseline':<22} {r['value']:>+7.3f}   [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] {sig}  p={r['p_two_sided']:.4f}")

print(f"\n(* = 95% CI of the delta excludes 0)")
print(f"\nWrote {OUT_CSV}")
