"""Script to patch the annotation tool HTML with student and reference data."""

import argparse
import json
import os
import sys

# Allow running from project root
sys.path.append(os.getcwd())

try:
    from scripts.common_utils import DEFAULT_OUTPUT_DIR
except ImportError:
    from common_utils import DEFAULT_OUTPUT_DIR


def patch_annotation_tool(student_data_file, reference_file, tool_html_file, output_file=None):
    """Embed student data and reference solutions into the annotation tool HTML."""

    with open(student_data_file) as f:
        student_data = json.load(f)

    with open(reference_file) as f:
        reference_data = json.load(f)

    with open(tool_html_file) as f:
        html = f.read()

    # Inject student data after the PROBLEMS constant
    student_js = f"\nconst STUDENT_DATA = {json.dumps(student_data)};\n"
    reference_js = f"\nconst REFERENCE_SOLUTIONS = {json.dumps(reference_data)};\n"

    # Find the injection point — after ALL_KCS definition
    inject_marker = 'const ALL_KCS = '
    if inject_marker not in html:
        print(
            f"ERROR: Could not find injection point '{inject_marker}' in {tool_html_file}")
        return None

    inject_idx = html.index(inject_marker)
    # Find end of that line
    line_end = html.index(';', inject_idx) + 1

    # Inject the data
    html = html[:line_end] + "\n" + student_js + reference_js + html[line_end:]

    # Now update the render function to use the embedded data
    # Replace the student code placeholder
    new_student_render = """// Auto-loaded from embedded data
  const sd2 = STUDENT_DATA[String(pid)];
  if (sd2) {
    document.getElementById('student-code').textContent = sd2.code;
    document.getElementById('student-code').classList.remove('empty');
    const score = sd2.score;
    const scoreEl = document.getElementById('score-display');
    scoreEl.textContent = Math.round(score * 100) + '%';
    scoreEl.className = 'score-value ' + (score >= 1 ? 'pass' : score > 0 ? 'partial' : 'fail');
    document.getElementById('score-label').textContent = 
      score >= 1 ? '(all test cases passed)' : score > 0 ? '(partial)' : '(zero)';
  } else {
    document.getElementById('student-code').textContent = 'No submission for this problem';
    document.getElementById('student-code').classList.add('empty');
    document.getElementById('score-display').textContent = '\\u2014';
    document.getElementById('score-display').className = 'score-value';
    document.getElementById('score-label').textContent = '';
  }

  // Reference solutions
  const ref = REFERENCE_SOLUTIONS[String(pid)];
  if (ref) {
    document.getElementById('reference-code').textContent = 
      '// Solution 1:\\n' + ref.solution1 + '\\n\\n// Solution 2:\\n' + ref.solution2;
    document.getElementById('reference-code').classList.remove('empty');
  } else {
    document.getElementById('reference-code').textContent = 'No reference solutions for this problem';
    document.getElementById('reference-code').classList.add('empty');
  }
  // END auto-loaded"""

    # Replace the old student code section in render()
    # Find the block that starts with "const sd = studentData[pid];"
    old_block_start = "  const sd = studentData[pid];"
    old_block_end = "document.getElementById('score-label').textContent = '';\n  }"

    if old_block_start in html:
        start = html.index(old_block_start)
        # Find the end of the if/else block
        end = html.index(old_block_end, start) + len(old_block_end)
        html = html[:start] + new_student_render + html[end:]
    else:
        print(
            f"Warning: Could not find block start '{old_block_start}' for code replacement.")

    # Save patched version
    if output_file is None:
        base = os.path.splitext(tool_html_file)[0]
        output_file = f"{base}_loaded.html"

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"Patched tool saved to {output_file}")
    print(f"Student problems loaded: {len(student_data)}")
    print(f"Reference solutions loaded: {len(reference_data)}")
    print(
        f"\nOpen {output_file} in your browser — everything is embedded, no server needed.")

    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Patch the annotation tool with student and reference data")
    parser.add_argument("--student-file", type=str, required=True,
                        help="Path to student_data_*.json")
    parser.add_argument("--ref-file", type=str, default=os.path.join(DEFAULT_OUTPUT_DIR, "reference_solutions.json"),
                        help="Path to reference_solutions.json")
    parser.add_argument("--html", type=str, required=True,
                        help="Path to the original kc_annotation_tool.html")
    parser.add_argument("--output", type=str,
                        help="Path to save the patched HTML file")

    args = parser.parse_args()

    patch_annotation_tool(
        args.student_file,
        args.ref_file,
        args.html,
        args.output
    )
