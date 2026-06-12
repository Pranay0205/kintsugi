"""Transient driver: execute exp21 notebook code cells top-to-bottom in one
namespace (same semantics as running the notebook in order). Not a deliverable."""
import json, sys
from pathlib import Path

nb_path = Path("/mnt/d/Projects/kintsugi/experiments/ablation/exp21_v3_ablation.ipynb")
nb = json.loads(nb_path.read_text())
ns = {"__name__": "__main__"}
code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
for i, c in enumerate(code_cells):
    src = "".join(c["source"])
    print(f"\n>>>>> EXEC CODE CELL {i+1}/{len(code_cells)} >>>>>", flush=True)
    exec(compile(src, f"<cell {i+1}>", "exec"), ns)
print("\nALL CELLS EXECUTED OK", flush=True)
