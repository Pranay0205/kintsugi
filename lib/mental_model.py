import json
import re
import time
from typing import Any

import networkx as nx
import pandas as pd
from google import genai
from google.genai import types

import lib.prompts
from lib.llm_batch_analyzer import format_submissions, clean_json_response
from utils.dataset import load_topics_json, load_problem_descriptions


def load_skill_map(prompts_path: str = "dataset/CodeWorkout/Problem_Prompts/problem_prompts.csv"):
    skill_df = pd.read_csv(prompts_path)
    skill_cols = skill_df.columns[3:]

    skill_map = {}
    for _, row in skill_df.iterrows():
        prob_id = row["ProblemID"]
        required_skills = [skill for skill in skill_cols if row[skill] == 1.0]
        skill_map[prob_id] = required_skills

    return skill_map, list(skill_cols)


def calculate_student_profile(student_id, attempts_df: pd.DataFrame, skill_map: dict, all_skills: list[str]) -> dict:
    student_work = attempts_df[attempts_df["SubjectID"] == student_id]
    skill_scores = {skill: [] for skill in all_skills}

    for _, row in student_work.iterrows():
        prob_id = row["ProblemID"]
        score = row["Score"]
        if prob_id in skill_map:
            for skill in skill_map[prob_id]:
                skill_scores[skill].append(score)

    return {
        skill: (sum(scores) / len(scores)) if scores else 0.0
        for skill, scores in skill_scores.items()
    }


def build_prerequisite_graph() -> nx.DiGraph:
    dependencies = [
        ("LogicCompareNum", "If/Else"),
        ("LogicBoolean", "If/Else"),
        ("If/Else", "NestedIf"),
        ("If/Else", "LogicAndNotOr"),
        ("For", "NestedFor"),
        ("While", "NestedFor"),
        ("ArrayIndex", "For"),
        ("StringIndex", "StringLen"),
        ("StringIndex", "StringEqual"),
        ("Math+-*/", "Math%"),
    ]
    graph = nx.DiGraph()
    graph.add_edges_from(dependencies)
    return graph


def get_weak_skills(profile: dict, threshold: float = 0.6) -> list[tuple[str, float]]:
    weak = [(skill, score) for skill, score in profile.items()
            if score > 0 and score < threshold]
    return sorted(weak, key=lambda item: item[1])


def get_prereq_risk_chains(graph: nx.DiGraph, weak_skill_pairs: list[tuple[str, float]], max_items: int = 8):
    weak = [skill for skill, _ in weak_skill_pairs]
    chains = []
    for skill in weak:
        if skill in graph:
            chains.append(
                {
                    "skill": skill,
                    "prerequisites": list(graph.predecessors(skill)),
                    "downstream_risks": list(graph.successors(skill)),
                }
            )
    return chains[:max_items]


def build_mental_model_payload(student_id, profile: dict, weak_skill_pairs: list[tuple[str, float]], graph: nx.DiGraph) -> dict:
    top_weak = [{"skill": s, "mastery": round(
        v, 3)} for s, v in weak_skill_pairs[:10]]
    top_strong = sorted(profile.items(), key=lambda x: x[1], reverse=True)
    top_strong = [{"skill": s, "mastery": round(
        v, 3)} for s, v in top_strong[:8] if v > 0]

    return {
        "student_id": str(student_id),
        "top_weak_skills": top_weak,
        "top_strong_skills": top_strong,
        "prerequisite_risk_chains": get_prereq_risk_chains(graph, weak_skill_pairs),
    }


def build_context_enriched_prompt(student_problem_ids: list[int], mental_model: dict) -> str:
    topics = load_topics_json() or {}
    problem_descriptions = load_problem_descriptions() or {}
    curriculum_prompt = lib.prompts.build_curriculum_aware_prompt(
        topics,
        problem_descriptions,
        student_problem_ids,
    )

    context = json.dumps(mental_model, indent=2)
    return (
        curriculum_prompt
        + "\n\nAdditional Student Mental Model Context (high-priority):\n"
        + context
        + "\n\nUse this context to better judge likely misconceptions and future risks."
    )


def run_prompt_for_row(
    submission_row,
    prompt_text: str,
    client: genai.Client,
    model_id: str,
    temperature: float = 0.3,
):
    formatted_input = format_submissions([submission_row.to_dict()])
    start_t = time.time()
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=formatted_input,
            config=types.GenerateContentConfig(
                system_instruction=prompt_text,
                temperature=temperature,
                response_mime_type="application/json",
            ),
        )
        text = response.text if response and response.text else "{}"
        parsed = json.loads(clean_json_response(text))
        return parsed, round(time.time() - start_t, 3), None
    except Exception as e:
        return None, round(time.time() - start_t, 3), str(e)


def extract_gap_tokens(output_obj: dict[str, Any] | Any) -> set[str]:
    if not isinstance(output_obj, dict):
        return set()

    gaps = output_obj.get("knowledge_gaps", [])
    tokens = set()
    for gap in gaps:
        if isinstance(gap, dict):
            val = gap.get("category") or gap.get(
                "gap") or gap.get("skill") or ""
        else:
            val = str(gap)

        for token in re.findall(r"[A-Za-z][A-Za-z0-9_+/\-]*", str(val)):
            tokens.add(token.lower())

    return tokens


def run_context_enriched_eval(
    eval_df: pd.DataFrame,
    student_id,
    weak_skills: list[tuple[str, float]],
    prompt_text: str,
    client: genai.Client,
    model_id: str,
) -> pd.DataFrame:
    weak_skill_tokens = {s.lower() for s, _ in weak_skills}
    rows = []

    for _, row in eval_df.iterrows():
        output_obj, elapsed_sec, run_err = run_prompt_for_row(
            submission_row=row,
            prompt_text=prompt_text,
            client=client,
            model_id=model_id,
        )
        out_tokens = extract_gap_tokens(output_obj)
        overlap = len(out_tokens.intersection(weak_skill_tokens))

        rows.append(
            {
                "SubjectID": student_id,
                "ProblemID": row["ProblemID"],
                "Score": row["Score"],
                "ContextEnriched_Output": output_obj if run_err is None else f"Error: {run_err}",
                "ContextEnriched_TimeSec": elapsed_sec,
                "ContextEnriched_WeakSkillOverlap": overlap,
            }
        )

    return pd.DataFrame(rows)


def summarize_context_eval(context_eval_df: pd.DataFrame, student_id) -> pd.DataFrame:
    summary = {
        "StudentID": student_id,
        "N_Evals": len(context_eval_df),
        "Avg_ContextEnriched_Time": round(context_eval_df["ContextEnriched_TimeSec"].mean(), 3),
        "Avg_ContextEnriched_WeakSkillOverlap": round(context_eval_df["ContextEnriched_WeakSkillOverlap"].mean(), 3),
        "Max_WeakSkillOverlap": int(context_eval_df["ContextEnriched_WeakSkillOverlap"].max()),
        "Min_WeakSkillOverlap": int(context_eval_df["ContextEnriched_WeakSkillOverlap"].min()),
    }
    return pd.DataFrame([summary])
