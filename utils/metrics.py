"""Reusable evaluation metric functions for KC gap annotation studies."""

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from irrCAC.raw import CAC

KC_COLUMNS = [
    "If/Else", "NestedIf", "While", "For", "NestedFor",
    "Math+-*/", "Math%", "LogicAndNotOr", "LogicCompareNum", "LogicBoolean",
    "StringFormat", "StringConcat", "StringIndex", "StringLen",
    "StringEqual", "CharEqual", "ArrayIndex", "DefFunction",
]


def problem_f1(set_a: set, set_b: set) -> float:
    """Per-problem F1 between two gap sets. Both-empty = 1.0."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    tp = len(set_a & set_b)
    if tp == 0:
        return 0.0
    precision = tp / len(set_b)
    recall = tp / len(set_a)
    return 2 * precision * recall / (precision + recall)


def problem_jaccard(set_a: set, set_b: set) -> float:
    """Per-problem Jaccard between two gap sets. Both-empty = 1.0."""
    if not set_a and not set_b:
        return 1.0
    return len(set_a & set_b) / len(set_a | set_b)


def compute_kappa(binary_a: list, binary_b: list) -> float:
    """Cohen's kappa from two lists of 0/1 decisions using sklearn."""
    return float(cohen_kappa_score(binary_a, binary_b))


def compute_gwet_ac1(binary_a: list, binary_b: list) -> dict:
    """Gwet's AC1 with 95% CI using irrCAC."""
    df = pd.DataFrame({"rater_x": binary_a, "rater_y": binary_b})
    cac = CAC(df)
    result = cac.gwet()
    coeff = result["est"]["coefficient_value"]
    ci = result["est"]["confidence_interval"]
    return {"ac1": float(coeff), "ci_low": float(ci[0]), "ci_high": float(ci[1])}


def evaluate_pair(
    anns_x: dict,
    anns_y: dict,
    pids: list,
    kc_columns: list,
) -> dict:
    """Full evaluation between two raters over a list of problem IDs.

    anns_x, anns_y: {pid_str: set_of_gap_strings}
    Returns dict with Comparison, Cohen_kappa, Gwet_AC1, AC1_CI_low,
    AC1_CI_high, Problem_F1, Jaccard.
    """
    f1s = []
    jaccards = []
    binary_x = []
    binary_y = []

    for pid in pids:
        gx = anns_x.get(pid, set())
        gy = anns_y.get(pid, set())
        f1s.append(problem_f1(gx, gy))
        jaccards.append(problem_jaccard(gx, gy))
        for kc in kc_columns:
            binary_x.append(1 if kc in gx else 0)
            binary_y.append(1 if kc in gy else 0)

    gwet = compute_gwet_ac1(binary_x, binary_y)
    return {
        "Comparison": "",
        "Cohen_kappa": compute_kappa(binary_x, binary_y),
        "Gwet_AC1": gwet["ac1"],
        "AC1_CI_low": gwet["ci_low"],
        "AC1_CI_high": gwet["ci_high"],
        "Problem_F1": float(np.mean(f1s)),
        "Jaccard": float(np.mean(jaccards)),
    }


def evaluate_llm_vs_humans(
    anns_ha: dict,
    anns_hb: dict,
    anns_llm: dict,
    pids: list,
    kc_columns: list,
) -> list:
    """Compute H-H ceiling, HA-LLM, HB-LLM, and AvgHuman-LLM.

    Returns list of 4 result dicts.
    """
    hh = evaluate_pair(anns_ha, anns_hb, pids, kc_columns)
    hh["Comparison"] = "H-A vs H-B (Ceiling)"

    ha_llm = evaluate_pair(anns_ha, anns_llm, pids, kc_columns)
    ha_llm["Comparison"] = "HA vs LLM V3"

    hb_llm = evaluate_pair(anns_hb, anns_llm, pids, kc_columns)
    hb_llm["Comparison"] = "HB vs LLM V3"

    avg = {
        "Comparison": "AvgHuman vs LLM V3",
        "Cohen_kappa": (ha_llm["Cohen_kappa"] + hb_llm["Cohen_kappa"]) / 2,
        "Gwet_AC1": (ha_llm["Gwet_AC1"] + hb_llm["Gwet_AC1"]) / 2,
        "AC1_CI_low": None,
        "AC1_CI_high": None,
        "Problem_F1": (ha_llm["Problem_F1"] + hb_llm["Problem_F1"]) / 2,
        "Jaccard": (ha_llm["Jaccard"] + hb_llm["Jaccard"]) / 2,
    }

    return [hh, ha_llm, hb_llm, avg]
