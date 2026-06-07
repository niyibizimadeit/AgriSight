"""
 Descriptive Statistical Analysis
Computes summary statistics per category and generates charts 1–5.

Output:
  - data/cleaned/descriptive_summary.csv
  - analysis/charts/01–05_*.png
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

# Try to use a font that supports Chinese, fall back gracefully
try:
    matplotlib.rcParams["font.family"] = "SimHei"
except Exception:
    pass  # Continue without Chinese font — labels still render in en mode

# ---- Language toggle: "zh" = Chinese, "en" = English ----
LANG = "en"   # "zh" for Chinese (requires SimHei font), "en" for English
T = {
    "zh": {
        "count_by_cat":   "各类目商品数量",
        "avg_sales_cat":  "各类目平均销量",
        "price_dist":     "价格分布",
        "cat_pie":        "类目占比",
        "price_tier":     "各价格区间平均销量",
        "ylabel_sales":   "平均销量",
    },
    "en": {
        "count_by_cat":   "Product Count by Category",
        "avg_sales_cat":  "Average Sales Volume by Category",
        "price_dist":     "Price Distribution",
        "cat_pie":        "Category Proportion",
        "price_tier":     "Average Sales by Price Tier",
        "ylabel_sales":   "Average Sales Volume",
    },
}[LANG]

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = pd.read_csv("data/cleaned/cleaned_data.csv")
print(f"Records: {len(df)}")
print(f"Categories: {df['category'].nunique()}")

# ---------------------------------------------------------------------------
# Summary statistics per category
# ---------------------------------------------------------------------------
summary = df.groupby("category").agg(
    count=("product_name", "count"),
    avg_price=("price", "mean"),
    avg_sales=("sales_volume", "mean"),
    avg_rating=("rating", "mean"),
    avg_reviews=("review_count", "mean"),
    promo_rate=("is_promoted", "mean"),
).round(2)

print("\nDescriptive Summary:")
print(summary)

os.makedirs("data/cleaned", exist_ok=True)
summary.to_csv("data/cleaned/descriptive_summary.csv")
print("\nSaved: data/cleaned/descriptive_summary.csv")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
charts_dir = "analysis/charts"
os.makedirs(charts_dir, exist_ok=True)

# --- Chart 1: Product count by category ---
fig, ax = plt.subplots(figsize=(8, 5))
summary["count"].plot(kind="bar", ax=ax, color="steelblue", edgecolor="white")
ax.set_title(T["count_by_cat"], fontsize=14, fontweight="bold")
ax.set_xlabel("")
ax.tick_params(axis="x", rotation=0)
plt.tight_layout()
plt.savefig(f"{charts_dir}/01_count_by_category.png", dpi=150)
plt.close()
print("  Chart 1: Count by category")

# --- Chart 2: Average sales volume by category ---
fig, ax = plt.subplots(figsize=(8, 5))
summary["avg_sales"].plot(kind="bar", ax=ax, color="darkorange", edgecolor="white")
ax.set_title(T["avg_sales_cat"], fontsize=14, fontweight="bold")
ax.set_ylabel(T["ylabel_sales"])
ax.set_xlabel("")
ax.tick_params(axis="x", rotation=0)
plt.tight_layout()
plt.savefig(f"{charts_dir}/02_avg_sales_by_category.png", dpi=150)
plt.close()
print("  Chart 2: Avg sales by category")

# --- Chart 3: Price distribution histogram ---
fig, ax = plt.subplots(figsize=(8, 5))
df["price"].hist(bins=50, ax=ax, color="seagreen", edgecolor="white", alpha=0.85)
ax.set_title(T["price_dist"], fontsize=14, fontweight="bold")
ax.set_xlabel("Price (¥)")
ax.set_ylabel("Frequency")
ax.axvline(df["price"].median(), color="red", linestyle="--", linewidth=1.5, label=f"Median: ¥{df['price'].median():.1f}")
ax.legend()
plt.tight_layout()
plt.savefig(f"{charts_dir}/03_price_distribution.png", dpi=150)
plt.close()
print("  Chart 3: Price distribution")

# --- Chart 4: Category pie chart ---
fig, ax = plt.subplots(figsize=(7, 7))
counts = df["category"].value_counts()
colors = ["#4CAF50", "#FF9800", "#2196F3", "#9C27B0", "#F44336"]
ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%",
       colors=colors, startangle=90, pctdistance=0.85)
ax.set_title(T["cat_pie"], fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{charts_dir}/04_category_pie.png", dpi=150)
plt.close()
print("  Chart 4: Category pie")

# --- Chart 5: Average sales by price tier ---
fig, ax = plt.subplots(figsize=(7, 5))
tier_order = ["budget", "mid", "premium"]
tier_colors = ["#4CAF50", "#FF9800", "#F44336"]
tier_means = df.groupby("price_tier")["sales_volume"].mean()
# Ensure order
tier_means = tier_means.reindex(tier_order)
tier_means.plot(kind="bar", ax=ax, color=tier_colors, edgecolor="white")
ax.set_title(T["price_tier"], fontsize=14, fontweight="bold")
ax.set_ylabel(T["ylabel_sales"])
ax.set_xlabel("Price Tier")
ax.tick_params(axis="x", rotation=0)
ax.set_xticklabels(["Budget (<¥20)", "Mid (¥20–80)", "Premium (>¥80)"])
plt.tight_layout()
plt.savefig(f"{charts_dir}/05_price_tier_vs_sales.png", dpi=150)
plt.close()
print("  Chart 5: Price tier vs sales")

# ---------------------------------------------------------------------------
# Additional stats for report
# ---------------------------------------------------------------------------
print(f"\n{'=' * 50}")
print(f"Overall Statistics")
print(f"{'=' * 50}")
print(f"  Total products:     {len(df)}")
print(f"  Avg price:          ¥{df['price'].mean():.2f}")
print(f"  Median price:       ¥{df['price'].median():.2f}")
print(f"  Avg sales volume:   {df['sales_volume'].mean():.0f}")
print(f"  Avg rating:         {df['rating'].mean():.2f}")
print(f"  Promotion rate:     {df['is_promoted'].mean() * 100:.1f}%")
print(f"  Top category:       {summary['count'].idxmax()} ({summary['count'].max()} products)")
print(f"  Highest avg price:  {summary['avg_price'].idxmax()} (¥{summary['avg_price'].max():.1f})")
print(f"  Highest avg sales:  {summary['avg_sales'].idxmax()} ({summary['avg_sales'].max():.0f})")
print(f"\n  All charts saved to {charts_dir}/")
