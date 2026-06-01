"""
Phase 6 — Correlation Analysis
Computes Pearson correlation matrix and generates charts 6–9.

Output: analysis/charts/06–09_*.png
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

# ---- Language toggle ----
LANG = "en"
T = {
    "zh": {
        "heatmap":       "相关性热力图",
        "rating_sales":  "评分 vs 销量",
        "reviews_sales": "评论数 vs 销量",
        "price_sales":   "价格 vs 销量 (按类目着色)",
    },
    "en": {
        "heatmap":       "Correlation Heatmap",
        "rating_sales":  "Rating vs Sales Volume",
        "reviews_sales": "Review Count vs Sales Volume",
        "price_sales":   "Price vs Sales Volume by Category",
    },
}[LANG]

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = pd.read_csv("data/cleaned/cleaned_data.csv")
charts_dir = "analysis/charts"
os.makedirs(charts_dir, exist_ok=True)

# Feature set for correlation
features = ["price", "sales_volume", "review_count", "rating", "is_promoted"]
corr = df[features].corr()

print("Pearson Correlation Matrix:")
print(corr.round(3))

# Key findings
print(f"\nKey correlations with sales_volume:")
for f in ["price", "review_count", "rating", "is_promoted"]:
    r = corr.loc["sales_volume", f]
    print(f"  sales_volume vs {f:15s}: r = {r:+.3f}")

# ---------------------------------------------------------------------------
# Chart 6: Correlation heatmap
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 6))
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f",
            mask=mask, vmin=-1, vmax=1, center=0,
            linewidths=0.5, square=True, ax=ax,
            annot_kws={"fontsize": 11})
ax.set_title(T["heatmap"], fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{charts_dir}/06_correlation_heatmap.png", dpi=150)
plt.close()
print("\n  Chart 6: Correlation heatmap")

# ---------------------------------------------------------------------------
# Chart 7: Rating vs sales scatter
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(df["rating"], df["sales_volume"], alpha=0.25, s=8, c="steelblue", edgecolors="none")
# Add trend line
z = np.polyfit(df["rating"], df["sales_volume"], 1)
p = np.poly1d(z)
x_line = np.linspace(df["rating"].min(), df["rating"].max(), 100)
ax.plot(x_line, p(x_line), "r--", linewidth=1.5, alpha=0.7)
ax.set_title(T["rating_sales"], fontsize=14, fontweight="bold")
ax.set_xlabel("Rating")
ax.set_ylabel("Sales Volume")
r_val = corr.loc["sales_volume", "rating"]
ax.text(0.95, 0.95, f"r = {r_val:+.3f}", transform=ax.transAxes,
        fontsize=11, ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
plt.tight_layout()
plt.savefig(f"{charts_dir}/07_rating_vs_sales.png", dpi=150)
plt.close()
print("  Chart 7: Rating vs sales")

# ---------------------------------------------------------------------------
# Chart 8: Reviews vs sales scatter
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(df["review_count"], df["sales_volume"], alpha=0.25, s=8, c="darkorange", edgecolors="none")
z = np.polyfit(df["review_count"], df["sales_volume"], 1)
p = np.poly1d(z)
x_line = np.linspace(df["review_count"].min(), df["review_count"].max(), 100)
ax.plot(x_line, p(x_line), "r--", linewidth=1.5, alpha=0.7)
ax.set_title(T["reviews_sales"], fontsize=14, fontweight="bold")
ax.set_xlabel("Review Count")
ax.set_ylabel("Sales Volume")
r_val = corr.loc["sales_volume", "review_count"]
ax.text(0.95, 0.95, f"r = {r_val:+.3f}", transform=ax.transAxes,
        fontsize=11, ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
plt.tight_layout()
plt.savefig(f"{charts_dir}/08_reviews_vs_sales.png", dpi=150)
plt.close()
print("  Chart 8: Reviews vs sales")

# ---------------------------------------------------------------------------
# Chart 9: Price vs sales by category (colored scatter)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6))
cat_colors = {"水果": "#4CAF50", "蔬菜": "#FF9800", "粮油": "#2196F3",
              "茶叶": "#9C27B0", "生鲜": "#F44336"}
cat_en = {"水果": "Fruits", "蔬菜": "Vegetables", "粮油": "Grains & Oils",
          "茶叶": "Tea", "生鲜": "Fresh Produce"}
for cat, group in df.groupby("category"):
    color = cat_colors.get(cat, "gray")
    ax.scatter(group["price"], group["sales_volume"], label=cat_en.get(cat, cat),
               alpha=0.3, s=8, color=color, edgecolors="none")

ax.set_title(T["price_sales"], fontsize=14, fontweight="bold")
ax.set_xlabel("Price (¥)")
ax.set_ylabel("Sales Volume")
ax.legend(title="Category", fontsize=9, markerscale=3)
r_val = corr.loc["sales_volume", "price"]
ax.text(0.95, 0.95, f"r = {r_val:+.3f}", transform=ax.transAxes,
        fontsize=11, ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
plt.tight_layout()
plt.savefig(f"{charts_dir}/09_price_vs_sales_by_category.png", dpi=150)
plt.close()
print("  Chart 9: Price vs sales by category")

# ---------------------------------------------------------------------------
# Interpretation
# ---------------------------------------------------------------------------
print(f"\n{'=' * 50}")
print("Correlation Analysis — Key Interpretations")
print(f"{'=' * 50}")

# Find strongest correlations with sales
sales_corr = corr["sales_volume"].drop("sales_volume").sort_values(ascending=False)
print(f"\nFactors correlated with sales volume (strongest first):")
for feat, val in sales_corr.items():
    strength = "strong" if abs(val) > 0.3 else "moderate" if abs(val) > 0.1 else "weak"
    direction = "positive" if val > 0 else "negative"
    print(f"  {feat:15s}: r = {val:+.3f}  ({strength} {direction})")

print(f"\nCharts saved to {charts_dir}/")
