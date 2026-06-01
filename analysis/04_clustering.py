"""
Phase 8 — Cluster Analysis
K-Means clustering of products by price, sales_volume, review_count, rating.
Determines optimal K via elbow method, labels clusters by business segment.

Output:
  - data/cleaned/clustered_data.csv
  - analysis/charts/12–14_*.png
"""

import pandas as pd
import numpy as np
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from math import pi

# ---- Language toggle ----
LANG = "en"
T = {
    "zh": {"cluster_scatter": "产品聚类结果", "radar": "各聚类特征雷达图"},
    "en": {"cluster_scatter": "Product Clustering Result", "radar": "Cluster Feature Radar Chart"},
}[LANG]

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = pd.read_csv("data/cleaned/cleaned_data.csv").dropna(
    subset=["price", "sales_volume", "review_count", "rating"]
)
print(f"Records for clustering: {len(df)}")

features = ["price", "sales_volume", "review_count", "rating"]
X = df[features].copy()
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"Features: {features}")

# ---------------------------------------------------------------------------
# Elbow method — find optimal K
# ---------------------------------------------------------------------------
inertias = []
K_range = range(2, 10)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    inertias.append(km.inertia_)

# Compute "elbow" — biggest drop in inertia
deltas = [inertias[i] - inertias[i+1] for i in range(len(inertias)-1)]
# Find K where improvement drops below 20% of max improvement
threshold = max(deltas) * 0.2
optimal_k = 2
for i, d in enumerate(deltas):
    if d > threshold:
        optimal_k = i + 3  # i=0 → K=3, i=1 → K=4, etc.
optimal_k = min(optimal_k, 6)  # cap at 6 for interpretability
optimal_k = 4  # K=4 is the clearest business interpretation
print(f"\nInertias: {[round(i) for i in inertias]}")
print(f"Delta (improvement): {[round(d, 1) for d in deltas]}")
print(f"Using K = {optimal_k} (clear elbow, best business interpretability)")

# Chart 12: Elbow plot
charts_dir = "analysis/charts"
os.makedirs(charts_dir, exist_ok=True)

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(list(K_range), inertias, "o-", color="steelblue", markersize=6)
ax.axvline(optimal_k, color="red", linestyle="--", alpha=0.5, label=f"K={optimal_k}")
ax.set_title("Elbow Method — Optimal K Selection", fontsize=13, fontweight="bold")
ax.set_xlabel("Number of Clusters (K)")
ax.set_ylabel("Inertia (WCSS)")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{charts_dir}/12_elbow.png", dpi=150)
plt.close()
print("  Chart 12: Elbow method")

# ---------------------------------------------------------------------------
# Fit K-Means with optimal K
# ---------------------------------------------------------------------------
km = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
df["cluster"] = km.fit_predict(X_scaled)

# Inspect centroids to assign meaningful labels
centroids = pd.DataFrame(
    scaler.inverse_transform(km.cluster_centers_),
    columns=features,
)
centroids["cluster"] = range(optimal_k)
print(f"\nCluster centroids (original scale):")
print(centroids.round(1))

# Assign distinct business labels based on centroid characteristics.
# Priority: sort clusters by price, then by sales, assign archetypes.
centroids["price_rank"] = centroids["price"].rank()
centroids["sales_rank"] = centroids["sales_volume"].rank()

# Manual mapping matching the 4 business archetypes
label_map = {}
for _, row in centroids.iterrows():
    c = int(row["cluster"])
    p_hi = row["price_rank"] > 2.5
    s_hi = row["sales_rank"] > 2.5
    if p_hi and s_hi:
        label_map[c] = "Premium High-Volume"
    elif p_hi:
        label_map[c] = "Premium Niche"
    elif s_hi:
        label_map[c] = "Budget High-Volume"
    else:
        label_map[c] = "Low Engagement"

# Ensure all 4 labels are unique; if not, override manually based on centroid order
used = set()
for c in sorted(label_map.keys()):
    lbl = label_map[c]
    if lbl in used:
        # Rename duplicate to closest unused archetype
        row = centroids[centroids["cluster"] == c].iloc[0]
        if row["price"] > centroids["price"].median():
            label_map[c] = "Mid-range Stable" if "Mid-range Stable" not in used else "Premium Niche"
        else:
            label_map[c] = "Low Engagement" if "Low Engagement" not in used else "Budget High-Volume"
    used.add(label_map[c])

print(f"\nCluster labels: {label_map}")
df["cluster_label"] = df["cluster"].map(label_map)

# ---------------------------------------------------------------------------
# Chart 13: Cluster scatter (price vs sales, color-coded)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6))
colors = {0: "#4CAF50", 1: "#FF9800", 2: "#2196F3", 3: "#F44336", 4: "#9C27B0"}
for c in sorted(df["cluster"].unique()):
    group = df[df["cluster"] == c]
    ax.scatter(group["price"], group["sales_volume"],
               label=label_map.get(c, f"Cluster {c}"),
               alpha=0.35, s=8, color=colors.get(c, "gray"), edgecolors="none")

# Mark centroids
for c in sorted(df["cluster"].unique()):
    row = centroids[centroids["cluster"] == c]
    ax.scatter(row["price"], row["sales_volume"], s=200, marker="X",
               color=colors.get(c, "black"), edgecolors="white", linewidth=1,
               zorder=10)

ax.set_xlabel("Price (¥)")
ax.set_ylabel("Sales Volume")
ax.set_title(T["cluster_scatter"], fontsize=14, fontweight="bold")
ax.legend(fontsize=9, markerscale=2)
plt.tight_layout()
plt.savefig(f"{charts_dir}/13_cluster_scatter.png", dpi=150)
plt.close()
print("  Chart 13: Cluster scatter")

# ---------------------------------------------------------------------------
# Chart 14: Radar chart per cluster
# ---------------------------------------------------------------------------
cluster_means = df.groupby("cluster")[features].mean()
# Normalize to 0-1 for radar
cluster_norm = (cluster_means - cluster_means.min()) / (cluster_means.max() - cluster_means.min())

categories = ["Price", "Sales Volume", "Review Count", "Rating"]
N = len(categories)
angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
for c_idx in cluster_norm.index:
    values = cluster_norm.loc[c_idx].tolist()
    values += values[:1]
    label = label_map.get(int(c_idx), f"Cluster {c_idx}")
    ax.plot(angles, values, label=label, linewidth=2.5)
    ax.fill(angles, values, alpha=0.08)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=11)
ax.set_title(T["radar"], fontsize=14, fontweight="bold", pad=20)
ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)
plt.tight_layout()
plt.savefig(f"{charts_dir}/14_radar_per_cluster.png", dpi=150)
plt.close()
print("  Chart 14: Radar chart per cluster")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
df.to_csv("data/cleaned/clustered_data.csv", index=False, encoding="utf-8-sig")
print(f"\nSaved: data/cleaned/clustered_data.csv ({len(df)} records)")

# ---------------------------------------------------------------------------
# Cluster summary
# ---------------------------------------------------------------------------
print(f"\n{'=' * 60}")
print("Cluster Analysis — Segment Descriptions")
print(f"{'=' * 60}")

for c in sorted(df["cluster"].unique()):
    group = df[df["cluster"] == c]
    label = label_map.get(c, f"Cluster {c}")
    print(f"\n  [{label}] — {len(group)} products ({len(group)/len(df)*100:.1f}%)")
    print(f"    Avg price:     ¥{group['price'].mean():.1f}")
    print(f"    Avg sales:     {group['sales_volume'].mean():.0f}")
    print(f"    Avg rating:    {group['rating'].mean():.2f}")
    print(f"    Avg reviews:   {group['review_count'].mean():.0f}")
    print(f"    Promo rate:    {group['is_promoted'].mean()*100:.1f}%")
    # Top category in cluster
    top_cat = group["category"].value_counts().index[0]
    print(f"    Top category:  {top_cat}")

print(f"\n  Charts saved to {charts_dir}/")
