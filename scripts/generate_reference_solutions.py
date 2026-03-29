"""Script to generate 2 correct reference solutions per problem using Gemini."""

from utils.constants import GEMINI_API_KEY
from utils.dataset import load_problem_topics
import argparse
import json
import os
import sys
import time

from google import genai

# Allow running from project root
sys.path.append(os.getcwd())


try:
    from scripts.common_utils import DEFAULT_OUTPUT_DIR, ensure_output_dir
except ImportError:
    from common_utils import DEFAULT_OUTPUT_DIR, ensure_output_dir


def generate_reference_solutions(data_dir=DEFAULT_OUTPUT_DIR, model_id="gemini-2.0-flash", sleep_sec=1.0):
    """Generate 2 correct reference solutions per problem using Gemini."""

    ensure_output_dir(data_dir)

    print("Loading problem topics using utils.dataset...")
    pp = load_problem_topics()
    if pp is None:
        print("ERROR: Failed to load problem topics.")
        return None

    kc_cols = list(pp.columns)[3:]

    # Configure Gemini
    # Uses GEMINI_API_KEY from utils.constants (loaded from .env)
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not found in environment. Check your .env file.")
        return None

    client = genai.Client(api_key=GEMINI_API_KEY)

    reference_solutions = {}
    total = len(pp)

    for idx, row in pp.iterrows():
        pid = str(int(row['ProblemID']))
        requirement = row['Requirement']
        required_kcs = [kc_cols[i] for i, v in enumerate(row[3:]) if v == 1]

        print(f"[{idx+1}/{total}] Problem {pid}...")

        prompt = f"""You are an experienced Java programming instructor.

PROBLEM:
{requirement}

This problem tests these Knowledge Components: {', '.join(required_kcs)}

Generate exactly 2 DIFFERENT correct Java solutions for this problem.
- Solution 1 should use one approach (e.g., if-else chain)
- Solution 2 should use a different approach (e.g., ternary operators, different logic structure)
- Both must be complete, compilable Java methods
- Do NOT include comments
- Make sure both solutions demonstrate the Knowledge Components listed above

Return as JSON:
{{
  "solution1": "public ... {{ ... }}",
  "solution2": "public ... {{ ... }}"
}}

Return ONLY the JSON, no other text."""

        try:
            # Note: GEMINI_API_KEY should be set in environment
            # If use is from .env, ensure it's loaded by Client() internally or set explicitly
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config={"temperature": 0.3, "max_output_tokens": 1000}
            )

            reply = response.text.strip()

            # Clean up markdown fences if present
            if reply.startswith("```"):
                reply = reply.split("\n", 1)[1]  # remove first line
            if reply.endswith("```"):
                reply = reply.rsplit("```", 1)[0]  # remove last fence
            reply = reply.strip()

            solutions = json.loads(reply)
            reference_solutions[pid] = {
                "solution1": solutions.get("solution1", "// Generation failed"),
                "solution2": solutions.get("solution2", "// Generation failed"),
                "required_kcs": required_kcs
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            reference_solutions[pid] = {
                "solution1": "// Generation failed — run again or write manually",
                "solution2": "// Generation failed — run again or write manually",
                "required_kcs": required_kcs
            }

        time.sleep(sleep_sec)

    # Save JSON
    output_file = os.path.join(data_dir, "reference_solutions.json")
    with open(output_file, 'w') as f:
        json.dump(reference_solutions, f, indent=2)

    success = sum(1 for v in reference_solutions.values()
                  if "failed" not in v["solution1"])
    print(f"\nSaved to {output_file}")
    print(f"Successful: {success}/{total}")

    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate reference solutions via Gemini SDK")
    parser.add_argument("--data-dir", type=str, default=DEFAULT_OUTPUT_DIR,
                        help="Directory to save output files")
    parser.add_argument("--model", type=str, default="gemini-2.0-flash",
                        help="Gemini model to use")
    parser.add_argument("--sleep", type=float, default=1.0,
                        help="Seconds to sleep between calls")
    args = parser.parse_args()

    generate_reference_solutions(
        data_dir=args.data_dir,
        model_id=args.model,
        sleep_sec=args.sleep
    )
