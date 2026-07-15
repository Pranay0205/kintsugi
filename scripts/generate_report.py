from lib.prompts import (
    get_chain_of_thought_prompt,
    get_few_shot_prompt,
    get_zero_shot_prompt,
)
import pandas as pd
import json
import ast
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def clean_json_string(s):
    if not isinstance(s, str):
        return {}
    try:
        # Try direct JSON parsing
        return json.loads(s)
    except:
        try:
            # Try evaluating as python dict (for single quotes)
            return ast.literal_eval(s)
        except:
            return s


STRATEGY_PROMPTS = {
    "Zero-Shot": get_zero_shot_prompt,
    "Few-Shot": get_few_shot_prompt,
    "Chain-of-Thought": get_chain_of_thought_prompt,
}

VISIBLE_STRATEGIES = ["Zero-Shot", "Few-Shot", "Chain-of-Thought"]


def generate_html_report(csv_file, output_html):
    df = pd.read_csv(csv_file)

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Student Assessment Analysis Report</title>
        <style>
            :root {
                --bg: #eef2f7;
                --card: #ffffff;
                --text: #0f172a;
                --muted: #475569;
                --accent: #0f62fe;
                --border: rgba(15, 23, 42, 0.08);
                --gap: #b91c1c;
            }
            * { box-sizing: border-box; }
            body {
                font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: var(--text);
                max-width: 1440px;
                margin: 0 auto;
                padding: 32px 24px 48px;
                background:
                    radial-gradient(circle at top left, rgba(15, 98, 254, 0.12), transparent 28%),
                    radial-gradient(circle at top right, rgba(14, 165, 233, 0.10), transparent 26%),
                    linear-gradient(180deg, #f8fafc 0%, var(--bg) 100%);
            }
            h1, h2, h3 { color: var(--text); margin: 0; }
            h1 { font-size: 2.2rem; letter-spacing: -0.03em; }
            h2 { font-size: 1.35rem; letter-spacing: -0.02em; }
            h3 { font-size: 1.05rem; letter-spacing: -0.01em; }
            .hero {
                background: linear-gradient(135deg, rgba(15, 98, 254, 0.10), rgba(14, 165, 233, 0.06));
                border: 1px solid var(--border);
                border-radius: 20px;
                padding: 24px 28px;
                margin-bottom: 28px;
                box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
            }
            .hero-subtitle { color: var(--muted); margin-top: 6px; max-width: 900px; }
            .card {
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 20px;
                padding: 28px;
                margin-bottom: 28px;
                box-shadow: 0 16px 36px rgba(15, 23, 42, 0.07);
                overflow: hidden;
            }
            .header-info {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 16px;
                padding-bottom: 16px;
                margin-bottom: 18px;
                border-bottom: 1px solid var(--border);
            }
            .meta-row { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 8px; }
            .pill {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                border-radius: 999px;
                font-size: 0.82rem;
                font-weight: 700;
                letter-spacing: 0.01em;
                background: #e2e8f0;
                color: #0f172a;
            }
            .score-high { background: #dcfce7; color: #166534; }
            .score-med { background: #fef3c7; color: #92400e; }
            .score-low { background: #fee2e2; color: #991b1b; }
            .prompt-box {
                background: linear-gradient(180deg, #fbfdff 0%, #f8fbff 100%);
                border: 1px solid rgba(15, 98, 254, 0.18);
                border-radius: 16px;
                padding: 18px 20px;
                margin-bottom: 14px;
            }
            .prompt-label {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                font-weight: 800;
                color: var(--accent);
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                font-size: 0.76rem;
            }
            .prompt-text {
                white-space: pre-wrap;
                font-size: 0.98rem;
                line-height: 1.7;
                color: #172033;
            }
            .code-block {
                background: linear-gradient(180deg, #0b1020 0%, #111827 100%);
                color: #e5e7eb;
                padding: 18px 20px;
                border-radius: 14px;
                overflow-x: auto;
                font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
                font-size: 0.92rem;
                margin: 10px 0 0;
                border: 1px solid rgba(255,255,255,0.08);
            }
            .assessment-stack {
                display: flex;
                flex-direction: column;
                gap: 18px;
                margin-top: 10px;
            }
            .strategy-section {
                border: 1px solid var(--border);
                border-top: 4px solid var(--accent);
                background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
                border-radius: 16px;
                padding: 18px;
            }
            .strategy-title {
                color: var(--accent);
                font-weight: 800;
                font-size: 1.02rem;
                margin-bottom: 10px;
                letter-spacing: -0.01em;
            }
            .gap-list { margin: 0; padding: 0 0 0 18px; }
            .gap-item {
                color: #7f1d1d;
                margin: 8px 0;
                padding-left: 2px;
            }
            .gap-item::marker { color: var(--gap); }
            .empty-state {
                margin: 0;
                color: var(--muted);
                font-style: italic;
            }
            .reasoning-box {
                margin-top: 14px;
                padding: 16px 18px;
                border-radius: 14px;
                background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
                border: 1px solid rgba(15, 23, 42, 0.08);
            }
            .reasoning-label {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 10px;
                font-weight: 800;
                color: #334155;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                font-size: 0.76rem;
            }
            .reasoning-text {
                white-space: pre-wrap;
                color: #1e293b;
                line-height: 1.7;
            }
            details summary {
                cursor: pointer;
                color: var(--accent);
                font-weight: 700;
                margin: 14px 0 0;
                outline: none;
                list-style: none;
            }
            details[open] summary { margin-bottom: 12px; }
            summary::-webkit-details-marker { display: none; }
            .lead-note { color: var(--muted); font-size: 0.96rem; margin-top: 10px; }
            .section-label {
                font-size: 0.78rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: #64748b;
                margin-bottom: 12px;
            }
        </style>
    </head>
    <body>
        <div class="hero">
            <h1>Student Assessment Analysis Report</h1>
            <p class="hero-subtitle">Prompt comparison output for thesis screenshots. Each card now shows the actual prompt sent to the LLM, the student code, and only the knowledge gaps from Zero-Shot, Few-Shot, and Chain-of-Thought.</p>
            <div class="meta-row">
                <span class="pill">Source: """ + html.escape(csv_file) + """</span>
                <span class="pill">Views: Prompt + Knowledge Gaps</span>
                <span class="pill">Optimized for slides</span>
            </div>
        </div>
    """

    for idx, row in df.iterrows():
        problem_id = row['ProblemID']
        score = row['Score']
        code = row['Code']

        score_class = "score-high" if score > 0.8 else (
            "score-low" if score < 0.6 else "score-med")

        html_content += f"""
        <div class="card">
            <div class="header-info">
                <div>
                    <div class="section-label">Problem {problem_id}</div>
                    <h2>Assessment Snapshot</h2>
                    <div class="lead-note">Use this card for a clean screenshot in a thesis defense deck.</div>
                </div>
                <span class="pill {score_class}">Score: {score:.2f}</span>
            </div>
            
            <details>
                <summary>View Student Code</summary>
                <div class="code-block"><pre>{html.escape(str(code))}</pre></div>
            </details>
            
            <h3>🤖 LLM Prompts and Knowledge Gaps</h3>
            <div class="assessment-stack">
        """

        strategies = [
            f"{name}_Output" for name in VISIBLE_STRATEGIES if f"{name}_Output" in df.columns]

        for strat_col in strategies:
            strategy_name = strat_col.replace("_Output", "").replace("_", " ")
            raw_data = row[strat_col]
            data = clean_json_string(raw_data)

            if isinstance(data, dict):
                # Handle Curriculum-Aware nested format
                if "student_analysis" in data and isinstance(data["student_analysis"], list) and len(data["student_analysis"]) > 0:
                    data = data["student_analysis"][0]

                # Start Strategy Section
                html_content += f"""
                <div class="strategy-section">
                    <div class="strategy-title">{strategy_name}</div>
                    <div class="prompt-box">
                        <div class="prompt-label">Actual Prompt Sent to LLM</div>
                        <div class="prompt-text">{html.escape(STRATEGY_PROMPTS[strategy_name]())}</div>
                    </div>
                """

                # Knowledge Gaps
                gaps = data.get("knowledge_gaps", [])
                if gaps:
                    html_content += "<div><strong>Knowledge Gaps:</strong><ul class='gap-list'>"
                    for g in gaps:
                        if isinstance(g, dict):
                            desc = g.get('gap') or g.get('category') or str(g)
                            html_content += f"<li class='gap-item'>{desc}</li>"
                        else:
                            html_content += f"<li class='gap-item'>{g}</li>"
                    html_content += "</ul></div>"
                else:
                    html_content += "<p class='empty-state'>No major gaps identified.</p>"

                if strategy_name == "Chain-of-Thought":
                    reasoning = data.get(
                        "reasoning_chain") or data.get("reasoning")
                    if reasoning:
                        if isinstance(reasoning, dict):
                            reasoning_html = "".join(
                                f"<p><strong>{html.escape(str(key))}:</strong> {html.escape(str(value))}</p>"
                                for key, value in reasoning.items()
                            )
                        else:
                            reasoning_html = html.escape(
                                str(reasoning)).replace("\n", "<br>")

                        html_content += f"""
                        <div class="reasoning-box">
                            <div class="reasoning-label">Reasoning</div>
                            <div class="reasoning-text">{reasoning_html}</div>
                        </div>
                        """

                html_content += "</div>"  # End strategy section
            else:
                html_content += f"""
                <div class="strategy-section">
                    <div class="strategy-title">{strategy_name}</div>
                    <p>{html.escape(str(data))}</p>
                </div>
                """

            html_content += "</div></div>"  # End assessment stack and card

    html_content += """
    </body>
    </html>
    """

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Report generated successfully: {output_html}")


if __name__ == "__main__":
    generate_html_report(
        "results/01_prompt_strategy_comparison/single_student_14355_exp3_results.csv", "results/assessment_report.html")
