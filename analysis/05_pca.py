"""
Phase 9 — PCA & Competitiveness Score
Principal Component Analysis for dimensionality reduction & composite scoring.
PC1 is used as a "competitiveness score" — higher = better overall product.

Output:
  - data/cleaned/final_data.csv
  - analysis/charts/15–16_*.png
"""

import pandas as pd
import numpy as np
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# ---- Language toggle ----
LANG = "en"
T = {
    "zh": {"top20": "Top 20 竞争力产品"},
    "en": {"top20": "Top 20 Most Competitive Products"},
}[LANG]

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = pd.read_csv("data/cleaned/clustered_data.csv").dropna(
    subset=["price", "sales_volume", "review_count", "rating", "is_promoted"]
)
print(f"Records for PCA: {len(df)}")

features = ["price", "sales_volume", "review_count", "rating", "is_promoted"]
X = df[features].copy()
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ---------------------------------------------------------------------------
# PCA
# ---------------------------------------------------------------------------
pca = PCA()
pca.fit(X_scaled)

# Explained variance
print(f"\nExplained variance per component:")
cumulative = 0
for i, (ratio, cum) in enumerate(zip(pca.explained_variance_ratio_,
                                       np.cumsum(pca.explained_variance_ratio_))):
    print(f"  PC{i+1}: {ratio*100:5.1f}%  (cumulative: {cum*100:.1f}%)")

# Component loadings
loadings = pd.DataFrame(
    pca.components_.T,
    index=features,
    columns=[f"PC{i+1}" for i in range(len(features))],
)
print(f"\nPC loadings (feature contributions):")
print(loadings.round(3))

# ---------------------------------------------------------------------------
# Chart 15: Scree plot
# ---------------------------------------------------------------------------
charts_dir = "analysis/charts"
os.makedirs(charts_dir, exist_ok=True)

fig, ax1 = plt.subplots(figsize=(8, 5))
bars = ax1.bar(range(1, len(features) + 1), pca.explained_variance_ratio_,
               color="steelblue", edgecolor="white", label="Individual")
ax1.set_xlabel("Principal Component")
ax1.set_ylabel("Explained Variance Ratio")
ax1.set_title("PCA Explained Variance (Scree Plot)", fontsize=14, fontweight="bold")

ax2 = ax1.twinx()
ax2.plot(range(1, len(features) + 1), np.cumsum(pca.explained_variance_ratio_),
         "ro-", linewidth=2, markersize=6, label="Cumulative")
ax2.set_ylabel("Cumulative Variance Ratio")
ax2.axhline(0.80, color="gray", linestyle="--", alpha=0.5, label="80% threshold")

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
plt.tight_layout()
plt.savefig(f"{charts_dir}/15_pca_scree.png", dpi=150)
plt.close()
print("  Chart 15: Scree plot")

# ---------------------------------------------------------------------------
# Competitiveness score (PC1)
# ---------------------------------------------------------------------------
pca2 = PCA(n_components=1)
scores = pca2.fit_transform(X_scaled).flatten()

# Check PC1 direction: should correlate positively with "good" metrics
pc1_sales_corr = np.corrcoef(scores, df["sales_volume"])[0, 1]
print(f"\nPC1 correlation with sales_volume: {pc1_sales_corr:.3f}")
# If PC1 is anti-correlated with sales, flip it
if pc1_sales_corr < 0:
    scores = -scores
    print("  Flipped PC1 sign (higher = better sales)")

df["competitiveness_score"] = scores

# Normalize to 0–100 for interpretability
score_min = df["competitiveness_score"].min()
score_max = df["competitiveness_score"].max()
df["competitiveness_score"] = (
    (df["competitiveness_score"] - score_min) / (score_max - score_min) * 100
)

# ---------------------------------------------------------------------------
# Chart 16: Top 20 competitive products
# ---------------------------------------------------------------------------
top20 = df.nlargest(20, "competitiveness_score")[
    ["product_name", "category", "competitiveness_score", "price", "sales_volume"]
].copy()

# Truncate long names
top20["short_name"] = top20["product_name"].apply(
    lambda x: (x[:55] + "...") if len(str(x)) > 55 else str(x)
)
# Add category prefix
top20["label"] = top20.apply(
    lambda r: f"[{r['category']}] {r['short_name']}", axis=1
)

fig, ax = plt.subplots(figsize=(9, 7))
colors_top = ["#F44336" if c == "茶叶" else "#FF9800" if c == "生鲜" else
              "#4CAF50" if c == "水果" else "#2196F3" if c == "粮油" else "#9C27B0"
              for c in top20["category"]]
ax.barh(range(20), top20["competitiveness_score"].values[::-1],
        color=colors_top[::-1], edgecolor="white", height=0.7)
ax.set_yticks(range(20))
ax.set_yticklabels(top20["label"].values[::-1], fontsize=7)
ax.set_xlabel("Competitiveness Score (0–100)")
ax.set_title(T["top20"], fontsize=14, fontweight="bold")
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(f"{charts_dir}/16_competitiveness_top20.png", dpi=150)
plt.close()
print("  Chart 16: Top 20 competitiveness")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
df.to_csv("data/cleaned/final_data.csv", index=False, encoding="utf-8-sig")
print(f"\nSaved: data/cleaned/final_data.csv ({len(df)} records)")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n{'=' * 60}")
print("PCA — Key Interpretations")
print(f"{'=' * 60}")
print(f"\n  PC1 explains: {pca.explained_variance_ratio_[0]*100:.1f}% of variance")
print(f"  PC1+PC2 explain: {pca.explained_variance_ratio_[:2].sum()*100:.1f}%")
print(f"  Components for 80%: {np.argmax(np.cumsum(pca.explained_variance_ratio_) >= 0.8) + 1}")

# Top PC1 contributors
pc1_loadings = loadings["PC1"].abs().sort_values(ascending=False)
print(f"\n  Top contributors to PC1 (competitiveness):")
for feat, val in pc1_loadings.items():
    direction = "+" if loadings.loc[feat, "PC1"] > 0 else "-"
    print(f"    {feat:18s}: {direction}{val:.3f}")

print(f"\n  Top 5 competitive products:")
for i, (_, row) in enumerate(top20.head(5).iterrows()):
    print(f"    [{i+1}] Score={row['competitiveness_score']:.0f}  "
          f"¥{row['price']:.0f}  Sales={row['sales_volume']:.0f}  "
          f"{row['short_name'][:50]}")

print(f"\n  Charts saved to {charts_dir}/")
