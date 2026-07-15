"""Re-cluster using only students with enough submission volume to be
annotatable (>=10 problems attempted, >=5 non-perfect), then plot where the
10-student validation cohort lands. This tests whether adding a data-volume
eligibility filter (instead of clustering on skill mastery alone) explains
why 4 cohort students fall outside the pure skill-based Struggling cluster.
"""
import pickle
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

with open(ROOT / 'scripts/_kmeans_eligible_cache.pkl', 'rb') as f:
    d = pickle.load(f)

sid_list = d['sid_list']
X_scaled = d['X_scaled']
cluster_names = d['cluster_names']
cohort_ids = d['cohort_ids']

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

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
        alpha=0.5,
        edgecolors='none',
        s=90,
    )

cohort_in_list = [sid for sid in cohort_ids if sid in sid_list]
cohort_missing = [sid for sid in cohort_ids if sid not in sid_list]
cohort_idx = [sid_list.index(sid) for sid in cohort_in_list]

ax.scatter(
    X_pca[cohort_idx, 0], X_pca[cohort_idx, 1],
    label=f"10-Student Validation Cohort (n={len(cohort_ids)})",
    facecolors='none',
    edgecolors='#d63031',
    linewidths=2.2,
    s=260,
    marker='o',
    zorder=5,
)

for sid, idx in zip(cohort_in_list, cohort_idx):
    x, y = X_pca[idx]
    ax.annotate(
        str(sid), (x, y),
        textcoords='offset points', xytext=(8, 6),
        fontsize=9, fontweight='bold', color='#d63031',
    )

ax.set_title(
    "10-Student Cohort vs. Clustering Restricted to Data-Sufficient Students\n"
    "(K-Means, K=3, on students with ≥10 problems & ≥5 non-perfect submissions)",
    fontsize=13,
)
ax.set_xlabel("Overall Skill Strength →")
ax.set_ylabel("Skill Profile Shape →")
ax.set_xticklabels([])
ax.set_yticklabels([])
ax.tick_params(left=False, bottom=False)
ax.legend(loc='best', fontsize=10)
ax.grid(alpha=0.25)
fig.tight_layout()

out_path = ROOT / 'results_consolidated/phase5_human_validation/kmeans_eligible_only_cohort.png'
fig.savefig(out_path, dpi=150)
print(f"Saved: {out_path}")
print(f"Cohort students not in eligible pool at all: {cohort_missing}")
