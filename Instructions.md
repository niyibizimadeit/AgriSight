# 📖 AgriSight — Build Instructions

Step-by-step technical instructions for each phase. Follow in order. Each phase builds on the previous.

---

## Phase 1 — Project Setup & Environment

### 1.1 Create the project structure

```bash
mkdir agrisight && cd agrisight
mkdir -p scraper data/raw data/cleaned analysis/charts backend/routes backend/models frontend/pages frontend/static db report
touch requirements.txt .gitignore .env README.md
```

### 1.2 Set up virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 1.3 requirements.txt

```
requests==2.31.0
selenium==4.18.1
beautifulsoup4==4.12.3
pandas==2.2.3
numpy==2.2.0
scipy==1.14.1
statsmodels==0.14.4
scikit-learn==1.6.0
matplotlib==3.10.0
seaborn==0.13.2
fastapi==0.115.0
uvicorn==0.34.0
python-dotenv==1.0.1
joblib==1.4.2
```

```bash
pip install -r requirements.txt
```

### 1.4 .env file

```
DB_PATH=data/agrisight.db
```

### 1.5 Database setup

SQLite is used for zero-configuration, portable storage — no server install needed. The database file is created automatically on first use.

```sql
-- db/schema.sql (reference DDL — SQLite creates tables via Python)
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_name TEXT,
  category TEXT,
  category_en TEXT,
  price REAL,
  sales_volume INTEGER,
  review_count INTEGER,
  rating REAL,
  origin TEXT,
  shipping_location TEXT,
  store_name TEXT,
  store_level TEXT,
  is_promoted INTEGER,
  product_url TEXT,
  price_tier TEXT,
  cluster_label TEXT,
  competitiveness_score REAL,
  scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

```python
# db/init_db.py — run once to create tables and import cleaned data
import sqlite3, os
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/agrisight.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
with open("db/schema.sql", encoding="utf-8") as f:
    conn.executescript(f.read())
conn.commit()
conn.close()
print(f"Database initialized at {DB_PATH}")
```

```bash
python db/init_db.py
```

---

## Phase 2 — Scraping Strategy & Target Selection

### 2.1 Target URLs (Suning 苏宁易购)

Use Suning's AJAX search endpoint for each category. Suning serves product data as HTML fragments — names, SKUs, and store info are in static HTML; prices require visiting individual product detail pages.

```
https://search.suning.com/emall/searchV1Product.do?keyword=新鲜水果&pg=01&cp=0
https://search.suning.com/emall/searchV1Product.do?keyword=新鲜蔬菜&pg=01&cp=0
https://search.suning.com/emall/searchV1Product.do?keyword=粮油调味&pg=01&cp=0
https://search.suning.com/emall/searchV1Product.do?keyword=茶叶&pg=01&cp=0
https://search.suning.com/emall/searchV1Product.do?keyword=生鲜肉禽&pg=01&cp=0
```

Collect at least 600 records per category to reach 3,000+ raw records (expect ~2,500+ after cleaning).

### 2.2 Inspect the page structure

Open a Suning search page in Chrome DevTools → Network tab → look for the XHR request to `searchV1Product.do`. The response is an HTML fragment with product cards:

```html
<li class="item-wrap 0000000000-SKU basic" hasprice="false">
  <div class="product-box">
    <div class="res-img">
      <div class="img-block">
        <a class="sellPoint" href="//product.suning.com/.../SKU.html">
          <img alt="Product Name" />
        </a>
      </div>
    </div>
    <div class="res-info">
      <div class="title-selling-point">
        <a href="//product.suning.com/.../SKU.html">Product Name</a>
      </div>
      <div class="price-box">
        <span class="def-price" datasku="SKU||zl|||VENDOR||"></span>
      </div>
    </div>
  </div>
</li>
```

Key selectors:
- Product name: `div.title-selling-point a`
- SKU: `span.def-price` → `datasku` attribute (first `|`-separated segment)
- Product URL: `a[href*='product.suning.com']`
- **Prices are JS-loaded** — the `<span class="def-price">` is empty in HTML; visit the product detail page to extract price, reviews, rating, and origin.

### 2.3 Rate limiting

Always add a delay between requests to avoid being blocked:

```python
import time, random
time.sleep(random.uniform(1.5, 3.5))
```

---

## Phase 3 — Scraper Development

### 3.1 suning_scraper.py skeleton

```python
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time, random, logging

logging.basicConfig(filename='scraper.log', level=logging.INFO)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

CATEGORIES = {
    "水果": "新鲜水果",
    "蔬菜": "新鲜蔬菜",
    "粮油": "粮油调味",
    "茶叶": "茶叶",
    "生鲜": "生鲜肉禽"
}

def scrape_category(keyword, category_label, max_pages=20):
    records = []
    for page in range(1, max_pages + 1):
        url = f"https://search.jd.com/Search?keyword={keyword}&page={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("#J_goodsList li[data-sku]")
            if not items:
                break
            for item in items:
                record = parse_item(item, category_label)
                if record:
                    records.append(record)
            logging.info(f"{category_label} page {page}: {len(items)} items")
            time.sleep(random.uniform(1.5, 3.5))
        except Exception as e:
            logging.error(f"Error on {category_label} page {page}: {e}")
    return records

def parse_item(item, category):
    try:
        name = item.select_one(".p-name em")
        price = item.select_one(".p-price strong i")
        reviews = item.select_one(".p-commit a")
        return {
            "product_name": name.text.strip() if name else None,
            "category": category,
            "price": price.text.strip() if price else None,
            "review_count": reviews.text.strip().replace("+", "") if reviews else None,
            "sales_volume": None,   # fill from product detail page if needed
            "rating": None,
            "origin": None,
            "shipping_location": None,
            "store_name": None,
            "store_level": None,
            "is_promoted": None,
            "product_url": None
        }
    except Exception as e:
        return None

if __name__ == "__main__":
    all_records = []
    for label, keyword in CATEGORIES.items():
        records = scrape_category(keyword, label)
        all_records.extend(records)
        print(f"{label}: {len(records)} records")

    df = pd.DataFrame(all_records)
    df.to_csv("data/raw/raw_data.csv", index=False, encoding="utf-8-sig")
    print(f"Total: {len(df)} records saved.")
```

> **Note:** Suning search pages are accessible via `requests`. If blocked, add longer delays or rotate User-Agent strings. Selenium (`webdriver.Chrome()`) is a fallback for JS-heavy pages.

---

## Phase 4 — Data Cleaning

### 4.1 cleaning.py

```python
import pandas as pd
import numpy as np
import re

df = pd.read_csv("data/raw/raw_data.csv")
print(f"Raw records: {len(df)}")

# --- Category mapping (Chinese → English) ---
CATEGORY_MAP = {
    "水果":     "Fruits",
    "蔬菜":     "Vegetables",
    "粮油":     "Grains & Oils",
    "粮油调味": "Grains & Oils",
    "茶叶":     "Tea",
    "生鲜":     "Fresh Produce",
    "生鲜肉禽": "Fresh Produce",
}
df["category_en"] = df["category"].map(CATEGORY_MAP).fillna("Other")

# --- Drop rows missing critical fields ---
df.dropna(subset=["product_name", "category", "price"], inplace=True)

# --- Parse price: "12.80" or "12.8~45.0" → take min price ---
def parse_price(val):
    if pd.isna(val): return np.nan
    nums = re.findall(r'\d+\.?\d*', str(val))
    return float(nums[0]) if nums else np.nan

df["price"] = df["price"].apply(parse_price)

# --- Parse sales volume: "1万+" → 10000, "358件" → 358 ---
def parse_sales(val):
    if pd.isna(val): return np.nan
    val = str(val)
    if "万" in val:
        num = re.findall(r'\d+\.?\d*', val)
        return int(float(num[0]) * 10000) if num else np.nan
    nums = re.findall(r'\d+', val)
    return int(nums[0]) if nums else np.nan

df["sales_volume"] = df["sales_volume"].apply(parse_sales)

# --- Fill missing sales with category median ---
df["sales_volume"] = df.groupby("category")["sales_volume"].transform(
    lambda x: x.fillna(x.median())
)

# --- Rating: fill with category median ---
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
df["rating"] = df.groupby("category")["rating"].transform(
    lambda x: x.fillna(x.median())
)

# --- Standardize promotion field ---
df["is_promoted"] = df["is_promoted"].apply(
    lambda x: 1 if str(x).lower() in ["true", "1", "yes", "促销", "优惠"] else 0
)

# --- Fill unknown origin ---
df["origin"] = df["origin"].fillna("未知")

# --- Remove duplicates ---
df.drop_duplicates(subset=["product_name", "price"], inplace=True)

# --- Remove outliers: cap at 99th percentile ---
for col in ["price", "sales_volume"]:
    upper = df[col].quantile(0.99)
    df[col] = df[col].clip(upper=upper)

# --- Add price tier ---
def price_tier(p):
    if p < 20: return "budget"
    elif p < 80: return "mid"
    else: return "premium"

df["price_tier"] = df["price"].apply(price_tier)

# --- Review density: reviews per unit sold (handle division by zero) ---
df["review_density"] = np.where(df["sales_volume"] > 0,
                                 df["review_count"] / df["sales_volume"],
                                 0)

print(f"Cleaned records: {len(df)}")
df.to_csv("data/cleaned/cleaned_data.csv", index=False, encoding="utf-8-sig")
```

---

## Phase 5 — Descriptive Statistical Analysis

### 5.1 01_descriptive.py

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'SimHei'  # Chinese font support

# ---- Language toggle: "zh" = Chinese, "en" = English ----
LANG = "zh"
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

df = pd.read_csv("data/cleaned/cleaned_data.csv")

# Summary stats per category (use category_en for English reports)
summary = df.groupby("category").agg(
    count=("product_name", "count"),
    avg_price=("price", "mean"),
    avg_sales=("sales_volume", "mean"),
    avg_rating=("rating", "mean")
).round(2)
print(summary)
summary.to_csv("data/cleaned/descriptive_summary.csv")

# Chart 1: Product count by category
summary["count"].plot(kind="bar", title=T["count_by_cat"])
plt.tight_layout()
plt.savefig("analysis/charts/01_count_by_category.png")
plt.clf()

# Chart 2: Avg sales by category
summary["avg_sales"].plot(kind="bar", color="orange", title=T["avg_sales_cat"])
plt.tight_layout()
plt.savefig("analysis/charts/02_avg_sales_by_category.png")
plt.clf()

# Chart 3: Price distribution histogram
df["price"].hist(bins=40, title=T["price_dist"])
plt.savefig("analysis/charts/03_price_distribution.png")
plt.clf()

# Chart 4: Category pie chart
df["category"].value_counts().plot(kind="pie", autopct="%1.1f%%", title=T["cat_pie"])
plt.savefig("analysis/charts/04_category_pie.png")
plt.clf()

# Chart 5: Average sales by price tier
df.groupby("price_tier")["sales_volume"].mean().plot(
    kind="bar", color=["green", "orange", "red"], title=T["price_tier"]
)
plt.ylabel(T["ylabel_sales"])
plt.tight_layout()
plt.savefig("analysis/charts/05_price_tier_vs_sales.png")
plt.clf()
```

---

## Phase 6 — Correlation Analysis

### 6.1 02_correlation.py

```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ---- Language toggle ----
LANG = "zh"
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

df = pd.read_csv("data/cleaned/cleaned_data.csv")
features = ["price", "sales_volume", "review_count", "rating", "is_promoted"]
corr = df[features].corr()

# Chart 6: Correlation heatmap
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
plt.title(T["heatmap"])
plt.tight_layout()
plt.savefig("analysis/charts/06_correlation_heatmap.png")
plt.clf()

# Chart 7: Rating vs sales scatter
df.plot.scatter(x="rating", y="sales_volume", alpha=0.3, title=T["rating_sales"])
plt.savefig("analysis/charts/07_rating_vs_sales.png")
plt.clf()

# Chart 8: Reviews vs sales scatter
df.plot.scatter(x="review_count", y="sales_volume", alpha=0.3, title=T["reviews_sales"])
plt.savefig("analysis/charts/08_reviews_vs_sales.png")
plt.clf()

# Chart 9: Price vs sales scatter (color-coded by category)
for cat, group in df.groupby("category"):
    plt.scatter(group["price"], group["sales_volume"], label=cat, alpha=0.3, s=10)
plt.xlabel("Price (¥)")
plt.ylabel("Sales Volume")
plt.legend(title="Category", fontsize=8)
plt.title(T["price_sales"])
plt.tight_layout()
plt.savefig("analysis/charts/09_price_vs_sales_by_category.png")
plt.clf()
```

---

## Phase 7 — Regression Analysis

### 7.1 03_regression.py

```python
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import statsmodels.api as sm

# ---- Language toggle ----
LANG = "zh"
T = {
    "zh": {"feat_imp": "特征重要性", "actual_pred": "实际销量 vs 预测销量"},
    "en": {"feat_imp": "Feature Importance", "actual_pred": "Actual vs Predicted Sales"},
}[LANG]

df = pd.read_csv("data/cleaned/cleaned_data.csv").dropna(
    subset=["price", "sales_volume", "review_count", "rating", "is_promoted", "category"]
)

# Encode category
le = LabelEncoder()
df["category_enc"] = le.fit_transform(df["category"])

features = ["price", "rating", "review_count", "is_promoted", "category_enc"]
X = df[features]
y = df["sales_volume"]

# OLS regression
X_ols = sm.add_constant(X)
model_ols = sm.OLS(y, X_ols).fit()
print(model_ols.summary())
with open("analysis/ols_summary.txt", "w") as f:
    f.write(str(model_ols.summary()))

# Random Forest
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)

print(f"MAE: {mean_absolute_error(y_test, y_pred):.2f}")
print(f"RMSE: {mean_squared_error(y_test, y_pred, squared=False):.2f}")
print(f"R²: {r2_score(y_test, y_pred):.4f}")

# Save model and encoder
joblib.dump(rf, "backend/models/rf_model.pkl")
joblib.dump(le, "backend/models/label_encoder.pkl")

# Chart 10: Feature importance
pd.Series(rf.feature_importances_, index=features).sort_values().plot(
    kind="barh", title=T["feat_imp"]
)
plt.tight_layout()
plt.savefig("analysis/charts/10_feature_importance.png")
plt.clf()

# Chart 11: Actual vs predicted sales
plt.scatter(y_test, y_pred, alpha=0.3, s=10)
plt.plot([y.min(), y.max()], [y.min(), y.max()], "r--", lw=1)
plt.xlabel("Actual Sales")
plt.ylabel("Predicted Sales")
plt.title(T["actual_pred"])
plt.tight_layout()
plt.savefig("analysis/charts/11_actual_vs_predicted.png")
plt.clf()
```

---

## Phase 8 — Cluster Analysis

### 8.1 04_clustering.py

```python
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# ---- Language toggle ----
LANG = "zh"
T = {
    "zh": {"cluster_scatter": "产品聚类结果", "radar": "各聚类特征雷达图"},
    "en": {"cluster_scatter": "Product Clustering Result", "radar": "Cluster Feature Radar Chart"},
}[LANG]

df = pd.read_csv("data/cleaned/cleaned_data.csv").dropna(
    subset=["price", "sales_volume", "review_count", "rating"]
)

features = ["price", "sales_volume", "review_count", "rating"]
X = df[features].copy()
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Elbow method
inertias = []
for k in range(2, 9):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    inertias.append(km.inertia_)

plt.plot(range(2, 9), inertias, "o-")
plt.title("Elbow Method")
plt.xlabel("K")
plt.ylabel("Inertia")
plt.savefig("analysis/charts/12_elbow.png")
plt.clf()

# Fit with K=4
km = KMeans(n_clusters=4, random_state=42, n_init=10)
df["cluster"] = km.fit_predict(X_scaled)

# Cluster labels (English — business segment names)
label_map = {0: "Budget High-Volume", 1: "Premium Niche", 2: "Mid-range Stable", 3: "Low Engagement"}
df["cluster_label"] = df["cluster"].map(label_map)

# Chart 13: cluster scatter
colors = {0: "blue", 1: "red", 2: "green", 3: "orange"}
for c, group in df.groupby("cluster"):
    plt.scatter(group["price"], group["sales_volume"], label=label_map[c],
                alpha=0.4, s=10, color=colors[c])
plt.xlabel("Price")
plt.ylabel("Sales Volume")
plt.legend()
plt.title(T["cluster_scatter"])
plt.savefig("analysis/charts/13_cluster_scatter.png")
plt.clf()

# Chart 14: radar chart per cluster
from math import pi
cluster_means = df.groupby("cluster")[features].mean()
categories = features
N = len(categories)
angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
for c_idx, row in cluster_means.iterrows():
    values = row.tolist()
    values += values[:1]
    ax.plot(angles, values, label=label_map[c_idx], linewidth=2)
    ax.fill(angles, values, alpha=0.1)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(["Price", "Sales Vol", "Reviews", "Rating"])
ax.set_title(T["radar"])
ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
plt.savefig("analysis/charts/14_radar_per_cluster.png")
plt.clf()

df.to_csv("data/cleaned/clustered_data.csv", index=False, encoding="utf-8-sig")
```

---

## Phase 9 — PCA & Competitiveness Score

### 9.1 05_pca.py

```python
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# ---- Language toggle ----
LANG = "zh"
T = {
    "zh": {"top20": "Top 20 竞争力产品"},
    "en": {"top20": "Top 20 Most Competitive Products"},
}[LANG]

df = pd.read_csv("data/cleaned/clustered_data.csv").dropna(
    subset=["price", "sales_volume", "review_count", "rating", "is_promoted"]
)

features = ["price", "sales_volume", "review_count", "rating", "is_promoted"]
X = df[features].copy()
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

pca = PCA()
pca.fit(X_scaled)

# Scree plot
plt.bar(range(1, len(features)+1), pca.explained_variance_ratio_)
plt.title("PCA Explained Variance")
plt.xlabel("Component")
plt.ylabel("Variance Ratio")
plt.savefig("analysis/charts/15_pca_scree.png")
plt.clf()

# Use PC1 as competitiveness score (flip sign if needed so higher = better)
pca2 = PCA(n_components=1)
scores = pca2.fit_transform(X_scaled).flatten()
df["competitiveness_score"] = -scores  # negate if PC1 anti-correlates with sales

# Top 20 chart
top20 = df.nlargest(20, "competitiveness_score")[["product_name", "competitiveness_score"]]
top20.set_index("product_name")["competitiveness_score"].plot(
    kind="barh", title=T["top20"]
)
plt.tight_layout()
plt.savefig("analysis/charts/16_competitiveness_top20.png")
plt.clf()

df.to_csv("data/cleaned/final_data.csv", index=False, encoding="utf-8-sig")
print("PCA complete. Final dataset saved.")
```

---

## Phase 10 — Backend API (FastAPI)

### 10.1 backend/db.py — Database connection utility

```python
import sqlite3, os
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/agrisight.db")

def get_connection():
    """Return a connection with row_factory set for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # better read concurrency
    return conn

def query(sql, params=()):
    """Run a SELECT query and return list of dicts."""
    conn = get_connection()
    cur = conn.execute(sql, params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows

def query_one(sql, params=()):
    """Run a SELECT query and return a single dict (or None)."""
    conn = get_connection()
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
```

### 10.2 backend/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import joblib, os

from routes import overview, products, analysis, predict

rf_model = None
label_encoder = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rf_model, label_encoder
    rf_model = joblib.load("models/rf_model.pkl")
    label_encoder = joblib.load("models/label_encoder.pkl")
    yield

app = FastAPI(title="AgriSight API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(overview.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(analysis.router, prefix="/api/analysis")
app.include_router(predict.router, prefix="/api")
```

### 10.3 Prediction endpoint (backend/routes/predict.py)

```python
from fastapi import APIRouter
from pydantic import BaseModel
import numpy as np

router = APIRouter()

class PredictRequest(BaseModel):
    price: float
    rating: float
    review_count: int
    is_promoted: int
    category: str

@router.post("/predict")
def predict_sales(req: PredictRequest):
    from main import rf_model, label_encoder
    try:
        cat_enc = label_encoder.transform([req.category])[0]
    except:
        cat_enc = 0
    X = np.array([[req.price, req.rating, req.review_count, req.is_promoted, cat_enc]])
    pred = rf_model.predict(X)[0]
    return {
        "predicted_sales": round(pred),
        "range_low": round(pred * 0.8),
        "range_high": round(pred * 1.2)
    }
```

> **Note on encoding:** The Random Forest model uses `LabelEncoder` for categories, which is acceptable for tree-based models. The OLS regression (Phase 7) uses the same encoding — for a more rigorous OLS, replace `LabelEncoder` with `pd.get_dummies()` one-hot encoding, but the RF model (used for predictions) is unaffected either way.

### 10.4 Run the server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Test: `http://localhost:8000/docs` (FastAPI auto-generates Swagger UI)

---

## Phase 11 — Frontend Development

> **Framework: Vue 3 (CDN)** — no build step, drop-in `<script>` tag. Each page is a standalone Vue app. ECharts and Tailwind CSS loaded via CDN.

### 11.1 Base HTML template

Every page includes Vue 3, ECharts, and Tailwind CSS from CDN:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AgriSight — {{ pageTitle }}</title>
  <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 font-sans">
  <div id="app">
    <!-- Page content here -->
  </div>
  <script>
    const { createApp, ref, reactive, onMounted, watch, computed } = Vue;
    createApp({
      setup() {
        // Component logic here
        return {};
      }
    }).mount("#app");
  </script>
</body>
</html>
```

### 11.2 Language Toggle (Bilingual Support)

All charts and UI support Chinese (`zh`) and English (`en`). Each page uses a reactive `lang` ref:

```javascript
const lang = ref(localStorage.getItem("agrisight_lang") || "zh");

const LABELS = {
  zh: { overview: "数据概览", products: "商品列表", predict: "销量预测" },
  en: { overview: "Data Overview", products: "Product List", predict: "Sales Prediction" },
};

function t(key) { return LABELS[lang.value]?.[key] || key; }

function switchLanguage(l) {
  lang.value = l;
  localStorage.setItem("agrisight_lang", l);
  // Charts re-render reactively via watchers
}
```

### 11.3 ECharts + Vue pattern

Use `ref` for the chart container DOM element, `onMounted` to initialise:

```javascript
setup() {
  const chartContainer = ref(null);
  let chartInstance = null;

  onMounted(() => {
    chartInstance = echarts.init(chartContainer.value);
    fetchChartData();
  });

  async function fetchChartData() {
    const res = await fetch("http://localhost:8000/api/analysis/sales-by-category");
    const data = await res.json();
    chartInstance.setOption({
      title: { text: t("avgSalesCat") },
      xAxis: { type: "category", data: data.categories },
      yAxis: { type: "value" },
      series: [{ type: "bar", data: data.values }],
    });
  }

  // Resize on window change
  window.addEventListener("resize", () => chartInstance?.resize());

  return { chartContainer };
}
```

```html
<div ref="chartContainer" style="width:100%;height:400px;"></div>
```

### 11.4 Prediction Widget (Vue)

Reactive form with two-way binding via `v-model`:

```html
<div id="predict-app" class="max-w-lg mx-auto p-6 bg-white rounded-xl shadow">
  <h2 class="text-xl font-bold mb-4">{{ t("predict") }}</h2>

  <label class="block mb-1 text-sm">Price (¥)</label>
  <input v-model.number="price" type="number" class="w-full border rounded px-3 py-2 mb-3" />

  <label class="block mb-1 text-sm">Rating (1–5)</label>
  <input v-model.number="rating" type="number" step="0.1" min="1" max="5"
         class="w-full border rounded px-3 py-2 mb-3" />

  <label class="block mb-1 text-sm">Review Count</label>
  <input v-model.number="reviewCount" type="number"
         class="w-full border rounded px-3 py-2 mb-3" />

  <label class="block mb-1 text-sm">Category</label>
  <select v-model="category" class="w-full border rounded px-3 py-2 mb-3">
    <option v-for="c in categories" :value="c">{{ c }}</option>
  </select>

  <label class="flex items-center gap-2 mb-4">
    <input v-model="isPromoted" type="checkbox" /> On Promotion
  </label>

  <button @click="predict" :disabled="loading"
          class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
    {{ loading ? "Predicting..." : "Predict Sales" }}
  </button>

  <div v-if="result" class="mt-4 p-4 bg-green-50 rounded text-center">
    Predicted: <b>{{ result.predicted_sales }}</b> units/month
    <br /><small>Range: {{ result.range_low }} – {{ result.range_high }}</small>
  </div>
</div>
```

```javascript
const { createApp, ref } = Vue;
createApp({
  setup() {
    const price = ref(null);
    const rating = ref(4.0);
    const reviewCount = ref(0);
    const category = ref("水果");
    const isPromoted = ref(false);
    const loading = ref(false);
    const result = ref(null);
    const categories = ["水果", "蔬菜", "粮油", "茶叶", "生鲜"];

    async function predict() {
      loading.value = true;
      result.value = null;
      try {
        const res = await fetch("http://localhost:8000/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            price: price.value,
            rating: rating.value,
            review_count: reviewCount.value,
            is_promoted: isPromoted.value ? 1 : 0,
            category: category.value,
          }),
        });
        result.value = await res.json();
      } finally {
        loading.value = false;
      }
    }

    return { price, rating, reviewCount, category, isPromoted,
             loading, result, categories, predict };
  }
}).mount("#predict-app");
```

---

## Phase 12 — Business Features & Polish

### Seller Benchmark feature

Add to `products.html` — after the product table, include:

```javascript
// Show where a given price/category sits vs competition
async function benchmark() {
  const res = await fetch("/api/products?category=" + selectedCategory);
  const data = await res.json();
  const prices = data.items.map(p => p.price).sort((a,b) => a-b);
  const userPrice = parseFloat(document.getElementById("my-price").value);
  const rank = prices.filter(p => p < userPrice).length;
  const pct = Math.round((rank / prices.length) * 100);
  alert(`Your price is higher than ${pct}% of competitors in this category.`);
}
```

### Price optimization tip

On the prediction page, after returning a prediction, also call a `/api/analysis/price-optimum?category=X` endpoint that returns the price range with the highest median sales in that category. Display as: *"Products in 水果 priced ¥15–¥35 see 40% higher average sales."*

---

## Phase 13 — Report Writing

> **Format: LaTeX → PDF**. Use `article` or `report` document class with `graphicx` for charts, `booktabs` for tables, and `hyperref` for links.

### Setup

```bash
mkdir -p report/figures
cp analysis/charts/*.png report/figures/
```

```latex
% report/agrisight_report.tex
\documentclass[12pt,a4paper]{article}
\usepackage[UTF8]{ctex}          % Chinese support
\usepackage{graphicx,booktabs,hyperref,geometry,caption,float}
\geometry{margin=2.5cm}
\title{AgriSight — Agricultural E-commerce Sales Analysis \& Prediction System}
\author{Your Name \\ Topic 3 — Medium Level}
\date{\today}
\begin{document}
\maketitle
\tableofcontents
\newpage
% ... sections ...
\end{document}
```

### Required sections

1. **Introduction** — project background, objectives, data source selection rationale
2. **Data Collection** — tools used, scraping methodology, target URLs, record counts
3. **Data Cleaning** — before/after table, each cleaning step explained, decisions justified
4. **Descriptive Analysis** — key stats, charts (`\includegraphics{figures/01_count_by_category.png}`), findings per category
5. **Correlation Analysis** — heatmap interpretation, notable correlations, business meaning
6. **Regression Analysis** — OLS summary interpretation (R², p-values), Random Forest results, which factors matter most
7. **Cluster Analysis** — K selection rationale, cluster descriptions, business interpretation of each segment
8. **PCA Analysis** — explained variance, competitiveness score methodology, top-ranked products
9. **Conclusions & Suggestions** — synthesize all findings into 5–8 actionable seller recommendations
10. **LLM Tool Usage** — list which parts used AI assistance and how results were manually validated

> Minimum 2,000 words. Include chart references (e.g. "As shown in Figure 5, ...").
> Compile: `pdflatex agrisight_report.tex` → `report/agrisight_report.pdf`

---

## Phase 14 — Defense PPT

### Slide guide

| Slide | Content |
|---|---|
| 1 | Title, name, topic (Topic 3 — Medium Level) |
| 2 | Problem statement: "Agricultural sellers lack market intelligence" |
| 3 | Data source, scraping approach, record counts |
| 4 | Data cleaning: before/after table + key cleaning decisions |
| 5 | Descriptive highlights: top categories, price/sales distributions |
| 6 | Correlation findings: what correlates with sales |
| 7 | Regression: top influencing factors + model accuracy |
| 8 | Clusters: 4 product tiers with characteristics |
| 9 | PCA: competitiveness score + top-ranked products |
| 10 | Prediction widget: live demo or screenshot |
| 11 | Key conclusions + 5 seller recommendations |
| 12 | System screenshots (all major pages) |

**Prepare verbal answers for:**
- Where data was collected from and why that source
- What each key field means
- Every cleaning decision made and why
- Why each analysis method was chosen
- What each chart shows and what conclusion it supports
- How the prediction model works
- Which parts used LLM tools vs manual work

---

## Phase 15 — Final Submission Package

### Checklist

```
submission/
├── 01_scraper_code/          # suning_scraper.py + generate_data.py + requirements.txt
├── 02_raw_data/              # raw_data.csv
├── 03_cleaned_data/          # cleaned_data.csv, final_data.csv, schema.sql, agrisight.db
├── 04_analysis_code/         # 01_descriptive.py ... 05_pca.py
├── 05_charts/                # all PNG chart exports
├── 06_web_system/            # backend/ + frontend/ full source
├── 07_report/                # agrisight_report.tex + agrisight_report.pdf
├── 08_defense_ppt/           # defense.pptx
└── 09_llm_usage/             # llm_tool_usage.docx
```

### Final verification

- [ ] All scripts run without errors from a clean directory
- [ ] Backend starts cleanly with `uvicorn main:app`
- [ ] All frontend pages load and render charts
- [ ] Prediction widget returns sensible output
- [ ] Report word count ≥ 2,000 words
- [ ] All 9 required charts present in both `/charts/` and rendered in the web system