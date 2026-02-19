import pandas as pd
import json
import ast


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
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f7; }
            h1, h2, h3 { color: #1d1d1f; }
            .card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
            .header-info { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 12px; margin-bottom: 16px; }
            .score-badge { background: #e5e5ea; padding: 4px 12px; border-radius: 999px; font-weight: bold; font-size: 0.9em; }
            .score-high { background: #d1fae5; color: #065f46; }
            .score-low { background: #fee2e2; color: #991b1b; }
            .code-block { background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 8px; overflow-x: auto; font-family: 'Menlo', 'Monaco', 'Courier New', monospace; font-size: 14px; margin: 10px 0; }
            .strategy-section { border-left: 4px solid #007aff; padding-left: 16px; margin-top: 20px; }
            .strategy-title { color: #007aff; font-weight: bold; font-size: 1.1em; margin-bottom: 8px; }
            .gap-item { color: #d93025; list-style-type: none; position: relative; padding-left: 20px; }
            .gap-item:before { content: "🔴"; position: absolute; left: 0; font-size: 0.8em; top: 3px; }
            .prediction-item { color: #8e44ad; list-style-type: none; position: relative; padding-left: 20px; }
            .prediction-item:before { content: "🔮"; position: absolute; left: 0; font-size: 0.8em; top: 3px; }
            .intervention-box { background: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 12px; margin-top: 10px; border-radius: 0 8px 8px 0; }
            .reasoning-box { background: #f3f4f6; border-left: 4px solid #6b7280; padding: 12px; margin-top: 10px; border-radius: 0 8px 8px 0; font-style: italic; }
            details summary { cursor: pointer; color: #007aff; font-weight: 500; margin: 10px 0; outline: none; }
        </style>
    </head>
    <body>
        <h1>Student Assessment Analysis Report</h1>
        <p>Generated from: """ + csv_file + """</p>
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
                <h2>Problem {problem_id}</h2>
                <span class="score-badge {score_class}">Score: {score:.2f}</span>
            </div>
            
            <details>
                <summary>View Student Code</summary>
                <div class="code-block"><pre>{code}</pre></div>
            </details>
            
            <h3>🤖 LLM Assessments</h3>
        """

        strategies = [col for col in df.columns if "_Output" in col]

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
                """

                # Knowledge Gaps
                gaps = data.get("knowledge_gaps", [])
                if gaps:
                    html_content += "<div style='margin-bottom: 10px;'><strong>Knowledge Gaps:</strong><ul>"
                    for g in gaps:
                        if isinstance(g, dict):
                            desc = g.get('gap') or g.get('category') or str(g)
                            html_content += f"<li class='gap-item'>{desc}</li>"
                        else:
                            html_content += f"<li class='gap-item'>{g}</li>"
                    html_content += "</ul></div>"
                else:
                    html_content += "<p><em>No major gaps identified.</em></p>"

                # Future Predictions
                predictions = data.get("future_predictions", [])
                if predictions:
                    html_content += "<div><strong>Future Predictions:</strong><ul>"
                    for p in predictions:
                        if isinstance(p, dict):
                            topic = p.get('at_risk_topic', '')
                            reason = p.get('reason', str(p))
                            html_content += f"<li class='prediction-item'><strong>{topic}:</strong> {reason}</li>"
                        else:
                            html_content += f"<li class='prediction-item'>{p}</li>"
                    html_content += "</ul></div>"

                # Interventions
                intervention = data.get("recommended_intervention")
                if intervention:
                    html_content += f"<div class='intervention-box'><strong>🎓 Intervention:</strong><br>{intervention}</div>"

                # Reasoning
                reasoning = data.get("reasoning_chain")
                if reasoning:
                    formatted_reasoning = ""
                    if isinstance(reasoning, dict):
                        for k, v in reasoning.items():
                            formatted_reasoning += f"<p><strong>{k}:</strong> {v}</p>"
                    else:
                        formatted_reasoning = reasoning
                    html_content += f"<div class='reasoning-box'><strong>🧠 Reasoning:</strong><br>{formatted_reasoning}</div>"

                html_content += "</div>"  # End strategy section
            else:
                html_content += f"""
                <div class="strategy-section">
                    <div class="strategy-title">{strategy_name}</div>
                    <p>{str(data)}</p>
                </div>
                """

        html_content += "</div>"  # End card

    html_content += """
    </body>
    </html>
    """

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Report generated successfully: {output_html}")


if __name__ == "__main__":
    generate_html_report(
        "student_14355_assessment_results.csv", "assessment_report.html")
