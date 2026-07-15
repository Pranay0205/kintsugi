"""Plot the final 10-struggling-student human-validation cohort (exp19/exp20/
final_4way) against the full-population K=3 skill-mastery clustering, so the
thesis defense slide shows exactly which students were selected and where
they sit relative to the whole class.
"""
import pickle
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

with open(ROOT / 'scripts/_kmeans_cohort_cache.pkl', 'rb') as f:
    d = pickle.load(f)

sid_list = d['sid_list']
X_pca = d['X_pca']
cluster_names = d['cluster_names']
cohort_ids = d['cohort_ids']
explained_var = d['explained_var']

COLORS = {
    'Struggling': '#54a0ff',
    'Average': '#ff9f43',
    'High Performer': '#1dd1a1',
}

fig, ax = plt.subplots(figsize=(12, 8))

for cname in ['High Performer', 'Average', 'Struggling']:
    mask = cluster_names == cname
    n = mask.sum()
    ax.scatter(
        X_pca[mask, 0], X_pca[mask, 1],
        label=f"{cname} (n={n})",
        color=COLORS[cname],
        alpha=0.35,
        edgecolors='none',
        s=60,
    )

cohort_idx = [sid_list.index(sid) for sid in cohort_ids]
ax.scatter(
    X_pca[cohort_idx, 0], X_pca[cohort_idx, 1],
    label=f"10-Student Validation Cohort (n={len(cohort_ids)})",
    facecolors='none',
    edgecolors='#d63031',
    linewidths=2.2,
    s=220,
    marker='o',
    zorder=5,
)

for sid, idx in zip(cohort_ids, cohort_idx):
    x, y = X_pca[idx]
    ax.annotate(
        str(sid), (x, y),
        textcoords='offset points', xytext=(8, 6),
        fontsize=9, fontweight='bold', color='#d63031',
    )

ax.set_title(
    "Where the 10 Validation Students Fall Among All Students",
    fontsize=14,
)
ax.set_xlabel("Overall Skill Strength →")
ax.set_ylabel("Skill Profile Shape →")
ax.set_xticklabels([])
ax.set_yticklabels([])
ax.tick_params(left=False, bottom=False)
ax.legend(loc='best', fontsize=10)
ax.grid(alpha=0.25)
fig.tight_layout()

out_path = ROOT / 'results_consolidated/phase5_human_validation/kmeans_10student_cohort.png'
fig.savefig(out_path, dpi=150)
print(f"Saved: {out_path}")
