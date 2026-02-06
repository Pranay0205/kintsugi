"""
Gap tag normalization for cross-strategy comparison.

LLM prompt strategies produce gap descriptions at different granularities:
  - Zero-Shot:          "**Loop Bounds and Off-by-One/Two Errors:**"
  - Curriculum-Aware:   "Loop"

This module maps any free-text tag to a canonical set so metrics
can be computed apples-to-apples across strategies.
"""

import re
from typing import List, Dict


CANONICAL_TAGS = [
    "Loop", "NestedLoop", "String", "Array", "Logic",
    "Condition", "Method", "Math", "Indexing", "Comparison",
]

# Keyword patterns → canonical tag  (order matters: first match wins)
_TAG_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"nested\s*(for|loop)", re.I), "NestedLoop"),
    (re.compile(
        r"\b(loop|iteration|while\s+loop|for\s+loop|off-by-one|off-by-two"
        r"|loop\s*bound|loop\s*termin|loop\s*index|loop\s*control"
        r"|loop\s*condition)\b", re.I), "Loop"),
    (re.compile(
        r"\b(string|substring|charAt|concat|indexOf|StringBuild|immutab"
        r"|text\s*process|char\s*arithmetic|string\s*manipul"
        r"|string\s*format)\b", re.I), "String"),
    (re.compile(r"\b(array|ArrayIndex)\b", re.I), "Array"),
    (re.compile(
        r"\b(logic|boolean|LogicAnd|LogicOr|LogicNot|logical\s*error"
        r"|conditional\s*logic|control\s*flow)\b", re.I), "Logic"),
    (re.compile(r"\b(condition|if.?else|branching|nested\s*if)\b", re.I), "Condition"),
    (re.compile(
        r"\b(method|function|return\s*type|method\s*signature"
        r"|overload|overrid|DefFunction)\b", re.I), "Method"),
    (re.compile(
        r"\b(math|arithmetic|modulo|Math[+\-*/]|numeric|modulus)\b", re.I), "Math"),
    (re.compile(
        r"\b(index|IndexOutOfBound|off-by|boundary|bounds|zero-based)\b", re.I), "Indexing"),
    (re.compile(r"\b(compar|equal|==|\.equals|relational)\b", re.I), "Comparison"),
]

# Canonical tag → problem_prompts.csv column names
TOPIC_COLUMN_MAP: dict[str, list[str]] = {
    "loop":       ["While", "For", "NestedFor"],
    "nestedloop": ["NestedFor"],
    "string":     ["StringFormat", "StringConcat", "StringIndex",
                   "StringLen", "StringEqual", "CharEqual"],
    "array":      ["ArrayIndex"],
    "logic":      ["LogicAndNotOr", "LogicCompareNum", "LogicBoolean"],
    "condition":  ["If/Else", "NestedIf", "LogicBoolean"],
    "method":     ["DefFunction"],
    "math":       ["Math+-*/", "Math%"],
    "indexing":   ["ArrayIndex", "StringIndex"],
    "comparison": ["LogicCompareNum", "StringEqual", "CharEqual"],
}


def normalize_gap_tag(raw_tag: str) -> str:
    """Map a verbose LLM gap tag to one of the ``CANONICAL_TAGS``."""
    cleaned = raw_tag.strip().strip("*").strip(":").strip()
    if cleaned in CANONICAL_TAGS:
        return cleaned

    for pattern, tag in _TAG_PATTERNS:
        if pattern.search(raw_tag):
            return tag

    return cleaned  # fallback: cleaned string for diagnostics


def normalize_predictions(predictions: List[Dict]) -> List[Dict]:
    """Normalize ``at_risk_topic`` / ``topic_tag`` values in a predictions list."""
    normalized = []
    for pred in predictions:
        new_pred = dict(pred)
        for key in ("at_risk_topic", "topic_tag", "category"):
            if key in new_pred and isinstance(new_pred[key], str):
                new_pred[key] = normalize_gap_tag(new_pred[key])
        normalized.append(new_pred)
    return normalized


def map_prediction_to_topic_columns(prediction_text: str) -> list[str]:
    """Map a prediction tag to the matching column names in ``problem_prompts.csv``."""
    tag = normalize_gap_tag(prediction_text)
    text = tag.lower()

    mapped: list[str] = []
    for key, columns in TOPIC_COLUMN_MAP.items():
        if key in text:
            mapped.extend(columns)

    return list(set(mapped))
