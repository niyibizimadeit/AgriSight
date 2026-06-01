"""
Phase 4 — Data Cleaning
Cleans raw agricultural product data: handles missing values, parses formats,
removes outliers and duplicates, adds derived columns.

Input:  data/raw/raw_data.csv
Output: data/cleaned/cleaned_data.csv
"""

import pandas as pd
import numpy as np
import re
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# 1. Load raw data
# ---------------------------------------------------------------------------
df = pd.read_csv("data/raw/raw_data.csv")
raw_count = len(df)
print(f"Raw records: {raw_count}")

# ---------------------------------------------------------------------------
# 2. Category mapping (Chinese → English)
# ---------------------------------------------------------------------------
CATEGORY_MAP = {
    "水果":     "Fruits",
    "蔬菜":     "Vegetables",
    "粮油":     "Grains & Oils",
    "粮油调味": "Grains & Oils",
    "茶叶":     "Tea",
    "生鲜":     "Fresh Produce",
    "生鲜肉禽": "Fresh Produce",
}
# Add category_en if not already present
if "category_en" not in df.columns or df["category_en"].isna().all():
    df["category_en"] = df["category"].map(CATEGORY_MAP).fillna("Other")

# ---------------------------------------------------------------------------
# 3. Drop rows missing critical fields
# ---------------------------------------------------------------------------
print(f"  Missing product_name: {df['product_name'].isna().sum()}")
print(f"  Missing category:      {df['category'].isna().sum()}")
print(f"  Missing price:         {df['price'].isna().sum()}")
df.dropna(subset=["product_name", "category", "price"], inplace=True)
print(f"  After dropping missing: {len(df)} records")

# ---------------------------------------------------------------------------
# 4. Parse and standardize numeric fields
# ---------------------------------------------------------------------------

# --- Price: handle both numeric and string formats ("¥12.80", "12.8~45.0") ---
def parse_price(val):
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    nums = re.findall(r"\d+\.?\d*", str(val))
    return float(nums[0]) if nums else np.nan

df["price"] = df["price"].apply(parse_price)

# --- Sales volume: handle "1万+" → 10000, "358件" → 358, or already numeric ---
def parse_sales(val):
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)):
        return int(val)
    val = str(val)
    if "万" in val:
        nums = re.findall(r"\d+\.?\d*", val)
        return int(float(nums[0]) * 10000) if nums else np.nan
    nums = re.findall(r"\d+", val)
    return int(nums[0]) if nums else np.nan

df["sales_volume"] = df["sales_volume"].apply(parse_sales)

# --- Review count: ensure integer ---
df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce")

# --- Rating: ensure float 1-5 ---
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
df["rating"] = df["rating"].clip(1.0, 5.0)

# ---------------------------------------------------------------------------
# 5. Fill missing values
# ---------------------------------------------------------------------------
print(f"\n  Before filling:")
print(f"    sales_volume nulls:  {df['sales_volume'].isna().sum()}")
print(f"    rating nulls:        {df['rating'].isna().sum()}")
print(f"    review_count nulls:  {df['review_count'].isna().sum()}")
print(f"    origin nulls:        {df['origin'].isna().sum()}")

# Fill with category median
df["sales_volume"] = df.groupby("category")["sales_volume"].transform(
    lambda x: x.fillna(x.median())
)
df["rating"] = df.groupby("category")["rating"].transform(
    lambda x: x.fillna(x.median())
)
df["review_count"] = df.groupby("category")["review_count"].transform(
    lambda x: x.fillna(0)
)
df["origin"] = df["origin"].fillna("未知")

# Ensure integer types after filling
df["sales_volume"] = df["sales_volume"].astype(int)
df["review_count"] = df["review_count"].astype(int)

print(f"  After filling:")
print(f"    sales_volume nulls:  {df['sales_volume'].isna().sum()}")
print(f"    rating nulls:        {df['rating'].isna().sum()}")
print(f"    review_count nulls:  {df['review_count'].isna().sum()}")
print(f"    origin nulls:        {df['origin'].isna().sum()}")

# ---------------------------------------------------------------------------
# 6. Standardize fields
# ---------------------------------------------------------------------------

# Promotion → binary
df["is_promoted"] = df["is_promoted"].apply(
    lambda x: 1 if str(x).lower() in ["true", "1", "1.0", "yes", "促销", "优惠"] else 0
)

# Category labels — strip whitespace
df["category"] = df["category"].str.strip()

# Fill missing shipping_location with origin
df["shipping_location"] = df["shipping_location"].fillna(df["origin"])

# ---------------------------------------------------------------------------
# 7. Remove duplicates
# ---------------------------------------------------------------------------
before_dedup = len(df)
df.drop_duplicates(subset=["product_name", "category"], inplace=True)
print(f"\n  Duplicates removed: {before_dedup - len(df)}")

# ---------------------------------------------------------------------------
# 8. Remove outliers (cap at 99th percentile)
# ---------------------------------------------------------------------------
for col in ["price", "sales_volume"]:
    p99 = df[col].quantile(0.99)
    outliers = (df[col] > p99).sum()
    df[col] = df[col].clip(upper=p99)
    print(f"  {col}: capped at {p99:.0f} (99th pct) — {outliers} values clipped")

# ---------------------------------------------------------------------------
# 9. Add derived columns
# ---------------------------------------------------------------------------

# Price tier
def price_tier(p):
    if p < 20:
        return "budget"
    elif p < 80:
        return "mid"
    else:
        return "premium"

if "price_tier" not in df.columns or df["price_tier"].isna().all():
    df["price_tier"] = df["price"].apply(price_tier)

# Review density (reviews per sale — engagement proxy)
df["review_density"] = np.where(
    df["sales_volume"] > 0,
    df["review_count"] / df["sales_volume"],
    0,
)

# ---------------------------------------------------------------------------
# 10. Save cleaned data
# ---------------------------------------------------------------------------
os.makedirs("data/cleaned", exist_ok=True)
df.to_csv("data/cleaned/cleaned_data.csv", index=False, encoding="utf-8-sig")
clean_count = len(df)

print(f"\n{'=' * 50}")
print(f"Cleaning Summary")
print(f"{'=' * 50}")
print(f"  Raw records:      {raw_count}")
print(f"  Cleaned records:  {clean_count}")
print(f"  Removed:          {raw_count - clean_count} ({(raw_count - clean_count) / raw_count * 100:.1f}%)")
print(f"  Output:           data/cleaned/cleaned_data.csv")

# Category breakdown
print(f"\n  Category breakdown (cleaned):")
for cat in df["category"].unique():
    subset = df[df["category"] == cat]
    print(f"    {cat:4s} ({subset['category_en'].iloc[0]:20s}): "
          f"{len(subset):4d} records  "
          f"avg price=¥{subset['price'].mean():.1f}  "
          f"avg sales={subset['sales_volume'].mean():.0f}")

# ---------------------------------------------------------------------------
# 11. Import into SQLite
# ---------------------------------------------------------------------------
DB_PATH = os.getenv("DB_PATH", "data/agrisight.db")
conn = sqlite3.connect(DB_PATH)
df.to_sql("products", conn, if_exists="replace", index=False)
conn.commit()
conn.close()
print(f"\n  Imported {clean_count} records into SQLite → {DB_PATH}")
