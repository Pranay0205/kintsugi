#!/usr/bin/env python3
"""Build a self-contained ablation comparison viewer."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ABLATION_DIR = ROOT / "results" / "human_validation" / "ablation"
STUDENT_DIR = ROOT / "scripts" / "annotation_tool" / "annotation_inputs"
HUMAN_DIR = ROOT / "dataset" / "Rater_KC_Tags"
OUTPUT = ROOT / "results" / "human_validation" / "ablation_viewer.html"

VERSION_ORDER = ["baseline", "reduced", "no_rules", "no_kc"]
VERSION_LABELS = {
    "baseline": "Baseline",
    "reduced": "Reduced",
    "no_rules": "No Rules",
    "no_kc": "No KC",
}
HUMAN_RATERS = {
    "Pranay Ghuge": {"key": "human_a", "label": "Human A", "short": "Pranay"},
    "Arundhati Das": {"key": "human_b", "label": "Human B", "short": "Arundhati"},
}
SOURCE_ORDER = ["human_a", "human_b", *VERSION_ORDER]
SOURCE_LABELS = {
    "human_a": "Human A",
    "human_b": "Human B",
    **VERSION_LABELS,
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def version_from_path(path: Path) -> tuple[str, str] | None:
    match = re.match(r"llm_ablation_(.+)_(\d+)\.json$", path.name)
    if not match:
        return None
    return match.group(1), match.group(2)


def collect_data() -> dict:
    students: dict[str, dict] = {}

    for path in sorted(ABLATION_DIR.glob("llm_ablation_*.json")):
        parsed = version_from_path(path)
        if not parsed:
            continue
        version, student_id = parsed
        result = load_json(path)
        student = students.setdefault(
            student_id,
            {
                "studentId": student_id,
                "humans": {},
                "versions": {},
                "submissions": {},
            },
        )
        student["versions"][version] = {
            "condition": result.get("condition", version),
            "rulesMode": result.get("rules_mode", ""),
            "kcMode": result.get("kc_mode", ""),
            "rater": result.get("rater", ""),
            "modelId": result.get("model_id", ""),
            "temperature": result.get("temperature"),
            "exportDate": result.get("exportDate", ""),
            "totalProblems": result.get("total_problems"),
            "totalAnnotated": result.get("totalAnnotated"),
            "totalCalls": result.get("total_calls"),
            "errors": result.get("errors", []),
            "annotations": result.get("annotations", {}),
            "rawResponses": result.get("raw_responses", {}),
        }

    for path in sorted(STUDENT_DIR.glob("student_*.json")):
        student_data = load_json(path)
        student_id = str(student_data.get("studentId") or path.stem.split("_")[-1])
        student = students.setdefault(
            student_id,
            {
                "studentId": student_id,
                "humans": {},
                "versions": {},
                "submissions": {},
            },
        )
        student["submissions"] = student_data.get("submissions", {})

    human_files: dict[tuple[str, str], tuple[int, Path]] = {}
    for path in HUMAN_DIR.rglob("kc_annotations_*.json"):
        if "discarded" in path.name:
            continue
        try:
            human_data = load_json(path)
        except json.JSONDecodeError:
            continue
        rater = human_data.get("rater")
        student_id = str(human_data.get("studentId", ""))
        if rater not in HUMAN_RATERS or not student_id:
            continue
        timestamp_match = re.search(r"_(\d+)\.json$", path.name)
        timestamp = int(timestamp_match.group(1)) if timestamp_match else 0
        key = (student_id, HUMAN_RATERS[rater]["key"])
        if key not in human_files or timestamp > human_files[key][0]:
            human_files[key] = (timestamp, path)

    for (student_id, human_key), (_, path) in human_files.items():
        if student_id not in students:
            continue
        human_data = load_json(path)
        rater = human_data.get("rater", "")
        student = students[student_id]
        student["humans"][human_key] = {
            "rater": rater,
            "label": HUMAN_RATERS.get(rater, {}).get("label", rater),
            "shortName": HUMAN_RATERS.get(rater, {}).get("short", rater),
            "exportDate": human_data.get("exportDate", ""),
            "totalAnnotated": human_data.get("totalAnnotated"),
            "sourceFile": str(path.relative_to(ROOT)),
            "annotations": human_data.get("annotations", {}),
        }

    for student in students.values():
        problem_ids = set(student["submissions"])
        for human in student["humans"].values():
            problem_ids.update(human["annotations"])
        for version in student["versions"].values():
            problem_ids.update(version["annotations"])
        student["problemIds"] = sorted(problem_ids, key=lambda pid: int(pid) if pid.isdigit() else pid)

    return {
        "generatedFrom": {
            "ablationDir": str(ABLATION_DIR.relative_to(ROOT)),
            "studentDir": str(STUDENT_DIR.relative_to(ROOT)),
            "humanDir": str(HUMAN_DIR.relative_to(ROOT)),
        },
        "sourceOrder": SOURCE_ORDER,
        "sourceLabels": SOURCE_LABELS,
        "versionOrder": VERSION_ORDER,
        "versionLabels": VERSION_LABELS,
        "students": dict(sorted(students.items(), key=lambda item: int(item[0]))),
    }


def html_template(data: dict) -> str:
    data_json = json.dumps(data, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ablation Study Viewer</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --panel-soft: #f0f4f8;
      --text: #17202a;
      --muted: #667085;
      --line: #d8dee6;
      --accent: #0f766e;
      --accent-soft: #d9f3ef;
      --warn: #b45309;
      --warn-soft: #fff2d8;
      --bad: #b42318;
      --bad-soft: #ffe4e0;
      --good: #1b7f45;
      --good-soft: #ddf7e8;
      --code: #101828;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.45 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    header {{
      position: sticky;
      top: 0;
      z-index: 10;
      background: rgba(247, 248, 250, 0.94);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(12px);
    }}

    .topbar {{
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto;
      gap: 16px;
      align-items: center;
      padding: 14px 18px;
    }}

    h1 {{
      margin: 0;
      font-size: 18px;
      font-weight: 760;
      letter-spacing: 0;
    }}

    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
      align-items: center;
    }}

    select, input, button {{
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      font: inherit;
    }}

    select, input {{
      padding: 6px 10px;
    }}

    input {{
      width: 240px;
    }}

    button {{
      padding: 6px 10px;
      cursor: pointer;
    }}

    button.active {{
      border-color: var(--accent);
      background: var(--accent-soft);
      color: #064e47;
    }}

    main {{
      display: grid;
      grid-template-columns: minmax(340px, 0.95fr) minmax(620px, 1.55fr);
      gap: 14px;
      padding: 14px;
      min-height: calc(100vh - 64px);
    }}

    .pane {{
      min-width: 0;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}

    .pane-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfd;
    }}

    .pane-title {{
      font-weight: 720;
    }}

    .meta {{
      color: var(--muted);
      font-size: 12px;
    }}

    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 8px;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
    }}

    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fff;
      min-width: 0;
    }}

    .metric strong {{
      display: block;
      font-size: 18px;
      line-height: 1.1;
      margin-bottom: 3px;
    }}

    .metric span {{
      color: var(--muted);
      font-size: 12px;
    }}

    .problem-list {{
      max-height: calc(100vh - 205px);
      overflow: auto;
    }}

    .problem-row {{
      display: grid;
      grid-template-columns: 58px 82px 1fr;
      gap: 10px;
      align-items: center;
      width: 100%;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      text-align: left;
      padding: 10px 12px;
      background: #fff;
    }}

    .problem-row:hover, .problem-row.selected {{
      background: var(--panel-soft);
    }}

    .pid {{
      font-weight: 760;
    }}

    .score {{
      font-variant-numeric: tabular-nums;
      color: var(--muted);
    }}

    .mini-gaps {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      min-width: 0;
    }}

    .chip {{
      display: inline-flex;
      align-items: center;
      max-width: 100%;
      border-radius: 999px;
      padding: 2px 7px;
      background: #eef2f6;
      color: #344054;
      font-size: 12px;
      white-space: nowrap;
    }}

    .chip.empty {{
      background: var(--good-soft);
      color: var(--good);
    }}

    .chip.diff {{
      background: var(--warn-soft);
      color: var(--warn);
    }}

    .detail {{
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      min-height: 0;
    }}

    .detail-body {{
      overflow: auto;
      max-height: calc(100vh - 116px);
    }}

    .code-wrap {{
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 10px;
      padding: 14px;
      border-bottom: 1px solid var(--line);
      background: #fff;
    }}

    pre {{
      margin: 0;
      padding: 12px;
      overflow: auto;
      border-radius: 8px;
      border: 1px solid #202939;
      background: var(--code);
      color: #eef4ff;
      font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
      tab-size: 2;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }}

    .versions {{
      display: grid;
      grid-template-columns: repeat(6, minmax(190px, 1fr));
      gap: 10px;
      padding: 14px;
    }}

    .version-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      min-width: 0;
      overflow: hidden;
    }}

    .version-head {{
      padding: 10px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfd;
    }}

    .version-title {{
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: center;
      font-weight: 740;
    }}

    .gaps {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 10px;
      min-height: 48px;
    }}

    details {{
      border-top: 1px solid var(--line);
    }}

    summary {{
      padding: 9px 10px;
      cursor: pointer;
      color: var(--muted);
      font-size: 12px;
    }}

    .reasoning {{
      padding: 0 10px 10px;
      color: #344054;
      font-size: 12px;
      white-space: pre-wrap;
    }}

    .missing {{
      color: var(--muted);
      padding: 10px;
    }}

    .only-diff .problem-row:not(.has-diff) {{
      display: none;
    }}

    @media (max-width: 1060px) {{
      main {{
        grid-template-columns: 1fr;
      }}
      .problem-list, .detail-body {{
        max-height: none;
      }}
      .versions, .summary {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}

    @media (max-width: 680px) {{
      .topbar {{
        grid-template-columns: 1fr;
      }}
      .controls {{
        justify-content: stretch;
      }}
      select, input, button {{
        width: 100%;
      }}
      .versions, .summary {{
        grid-template-columns: 1fr;
      }}
      .problem-row {{
        grid-template-columns: 48px 70px 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div>
        <h1>Ablation Study Viewer</h1>
        <div class="meta" id="sourceMeta"></div>
      </div>
      <div class="controls">
        <select id="studentSelect" aria-label="Student"></select>
        <input id="searchInput" type="search" placeholder="Search problem, KC, or code" aria-label="Search">
        <button id="diffToggle" type="button" title="Show only problems where versions disagree">Differences</button>
      </div>
    </div>
  </header>
  <main id="app">
    <section class="pane">
      <div class="pane-head">
        <div>
          <div class="pane-title" id="studentTitle"></div>
          <div class="meta" id="studentMeta"></div>
        </div>
        <div class="meta" id="problemCount"></div>
      </div>
      <div class="summary" id="summary"></div>
      <div class="problem-list" id="problemList"></div>
    </section>
    <section class="pane detail">
      <div class="pane-head">
        <div>
          <div class="pane-title" id="problemTitle"></div>
          <div class="meta" id="problemMeta"></div>
        </div>
      </div>
      <div class="detail-body" id="detailBody"></div>
    </section>
  </main>
  <script>
    const DATA = {data_json};
    const state = {{
      studentId: Object.keys(DATA.students)[0],
      problemId: null,
      search: "",
      onlyDiff: false,
    }};

    const el = (id) => document.getElementById(id);
    const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (ch) => ({{
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "\\"": "&quot;", "'": "&#39;"
    }}[ch]));

    function sourceRecord(student, source) {{
      if (source === "human_a" || source === "human_b") return student.humans[source] || null;
      return student.versions[source] || null;
    }}

    function gapsFor(student, source, pid) {{
      return sourceRecord(student, source)?.annotations?.[pid]?.gaps || [];
    }}

    function annotationFor(student, source, pid) {{
      return sourceRecord(student, source)?.annotations?.[pid] || null;
    }}

    function rawFor(student, source, pid) {{
      return student.versions[source]?.rawResponses?.[pid] || null;
    }}

    function normalizedSignature(student, pid) {{
      return DATA.sourceOrder.map((source) => gapsFor(student, source, pid).slice().sort().join("|")).join("::");
    }}

    function hasDiff(student, pid) {{
      const signatures = DATA.sourceOrder
        .filter((source) => sourceRecord(student, source))
        .map((source) => gapsFor(student, source, pid).slice().sort().join("|"));
      return new Set(signatures).size > 1;
    }}

    function allKcs(student, pid) {{
      const kcs = new Set();
      DATA.sourceOrder.forEach((source) => gapsFor(student, source, pid).forEach((kc) => kcs.add(kc)));
      return [...kcs].sort();
    }}

    function scoreLabel(score) {{
      return Number.isFinite(Number(score)) ? Number(score).toFixed(3).replace(/0+$/, "").replace(/\\.$/, "") : "n/a";
    }}

    function renderStudentOptions() {{
      el("studentSelect").innerHTML = Object.keys(DATA.students).map((studentId) =>
        `<option value="${{studentId}}">Student ${{studentId}}</option>`
      ).join("");
      el("studentSelect").value = state.studentId;
      el("sourceMeta").textContent = `${{DATA.generatedFrom.ablationDir}} + ${{DATA.generatedFrom.humanDir}} + ${{DATA.generatedFrom.studentDir}}`;
    }}

    function studentSummary(student) {{
      return DATA.sourceOrder.map((source) => {{
        const result = sourceRecord(student, source);
        if (!result) {{
          return `<div class="metric"><strong>n/a</strong><span>${{DATA.sourceLabels[source]}}</span></div>`;
        }}
        const annotations = result.annotations || {{}};
        const problemIds = Object.keys(annotations);
        const flagged = problemIds.filter((pid) => (annotations[pid].gaps || []).length).length;
        const totalGaps = problemIds.reduce((sum, pid) => sum + (annotations[pid].gaps || []).length, 0);
        const uniqueKcs = new Set(problemIds.flatMap((pid) => annotations[pid].gaps || [])).size;
        return `<div class="metric">
          <strong>${{flagged}}/${{problemIds.length}}</strong>
          <span>${{DATA.sourceLabels[source]}} flagged, ${{totalGaps}} gaps, ${{uniqueKcs}} KCs</span>
        </div>`;
      }}).join("");
    }}

    function problemMatches(student, pid) {{
      const query = state.search.trim().toLowerCase();
      if (!query) return true;
      const sub = student.submissions[pid] || {{}};
      const haystack = [
        pid,
        sub.code,
        sub.score,
        ...allKcs(student, pid),
        ...DATA.sourceOrder.flatMap((source) => {{
          const raw = rawFor(student, source, pid);
          const ann = annotationFor(student, source, pid);
          return [DATA.sourceLabels[source], ann?.notes, raw?.parsed_response?.reasoning, raw?.raw_response];
        }}),
      ].join("\\n").toLowerCase();
      return haystack.includes(query);
    }}

    function renderProblemList(student) {{
      const rows = student.problemIds.filter((pid) => problemMatches(student, pid));
      if (!rows.includes(state.problemId)) {{
        state.problemId = rows[0] || student.problemIds[0] || null;
      }}
      el("problemCount").textContent = `${{rows.length}} of ${{student.problemIds.length}} problems`;
      el("problemList").innerHTML = rows.map((pid) => {{
        const sub = student.submissions[pid] || {{}};
        const diff = hasDiff(student, pid);
        const chips = allKcs(student, pid).slice(0, 5).map((kc) => `<span class="chip ${{diff ? "diff" : ""}}">${{escapeHtml(kc)}}</span>`).join("") ||
          `<span class="chip empty">No gaps</span>`;
        return `<button class="problem-row ${{pid === state.problemId ? "selected" : ""}} ${{diff ? "has-diff" : ""}}" data-pid="${{pid}}">
          <span class="pid">#${{pid}}</span>
          <span class="score">score ${{scoreLabel(sub.score)}}</span>
          <span class="mini-gaps">${{chips}}</span>
        </button>`;
      }}).join("") || `<div class="missing">No matching problems.</div>`;
      el("problemList").classList.toggle("only-diff", state.onlyDiff);
      [...document.querySelectorAll(".problem-row")].forEach((row) => {{
        row.addEventListener("click", () => {{
          state.problemId = row.dataset.pid;
          render();
        }});
      }});
    }}

    function renderDetail(student) {{
      const pid = state.problemId;
      if (!pid) {{
        el("problemTitle").textContent = "No problem selected";
        el("problemMeta").textContent = "";
        el("detailBody").innerHTML = "";
        return;
      }}
      const sub = student.submissions[pid] || {{}};
      const union = allKcs(student, pid);
      el("problemTitle").textContent = `Problem #${{pid}}`;
      el("problemMeta").textContent = `Score ${{scoreLabel(sub.score)}} · ${{hasDiff(student, pid) ? "versions disagree" : "versions match"}} · ${{union.length}} unique KCs`;

      const versionCards = DATA.sourceOrder.map((source) => {{
        const result = sourceRecord(student, source);
        if (!result) {{
          return `<article class="version-card"><div class="version-head"><div class="version-title">${{DATA.sourceLabels[source]}}</div></div><div class="missing">Missing annotation</div></article>`;
        }}
        const gaps = gapsFor(student, source, pid);
        const raw = rawFor(student, source, pid);
        const ann = annotationFor(student, source, pid);
        const reasoning = raw?.parsed_response?.reasoning || raw?.raw_response || "";
        const score = raw?.score ?? sub.score;
        const isHuman = source === "human_a" || source === "human_b";
        const subtitle = isHuman
          ? `${{escapeHtml(result.shortName || result.rater || "")}}${{ann?.timestamp ? " / " + escapeHtml(ann.timestamp.slice(0, 10)) : ""}}`
          : `${{escapeHtml(result.rulesMode)}} / ${{escapeHtml(result.kcMode)}}`;
        const detailText = isHuman ? (ann?.notes || "No notes for this human annotation.") : (reasoning || "No raw response for this problem.");
        return `<article class="version-card">
          <div class="version-head">
            <div class="version-title"><span>${{DATA.sourceLabels[source]}}</span><span class="meta">${{isHuman ? "" : scoreLabel(score)}}</span></div>
            <div class="meta">${{subtitle}}</div>
          </div>
          <div class="gaps">
            ${{gaps.length ? gaps.map((kc) => `<span class="chip">${{escapeHtml(kc)}}</span>`).join("") : `<span class="chip empty">No gaps</span>`}}
          </div>
          <details>
            <summary>${{isHuman ? "Notes" : "Reasoning"}}</summary>
            <div class="reasoning">${{escapeHtml(detailText)}}</div>
          </details>
        </article>`;
      }}).join("");

      el("detailBody").innerHTML = `
        <div class="code-wrap">
          <div class="meta">Student code</div>
          <pre>${{escapeHtml(sub.code || "No code found for this problem.")}}</pre>
        </div>
        <div class="versions">${{versionCards}}</div>
      `;
    }}

    function render() {{
      const student = DATA.students[state.studentId];
      const diffCount = student.problemIds.filter((pid) => hasDiff(student, pid)).length;
      el("studentTitle").textContent = `Student ${{state.studentId}}`;
      el("studentMeta").textContent = `${{Object.keys(student.humans).length}} human raters · ${{Object.keys(student.versions).length}} ablation versions · ${{student.problemIds.length}} problems · ${{diffCount}} disagreements`;
      el("summary").innerHTML = studentSummary(student);
      el("diffToggle").classList.toggle("active", state.onlyDiff);
      renderProblemList(student);
      renderDetail(student);
    }}

    el("studentSelect").addEventListener("change", (event) => {{
      state.studentId = event.target.value;
      state.problemId = null;
      render();
    }});
    el("searchInput").addEventListener("input", (event) => {{
      state.search = event.target.value;
      render();
    }});
    el("diffToggle").addEventListener("click", () => {{
      state.onlyDiff = !state.onlyDiff;
      render();
    }});

    renderStudentOptions();
    render();
  </script>
</body>
</html>
"""


def main() -> None:
    data = collect_data()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html_template(data), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print(f"Students: {len(data['students'])}")
    print(f"Versions: {', '.join(data['versionOrder'])}")


if __name__ == "__main__":
    main()
