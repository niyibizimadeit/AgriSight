# ✅ AgriSight — TODO
> **Data source: Suning (苏宁易购)** — JD.com is JS-rendered + blocked, 1688 requires login. Suning serves product names/SKUs/stores in static HTML; prices from detail pages.
> **Target: 3,000+ raw records** (~600 per category, ~2,500+ after cleaning).

All tasks organized by phase. Check off items as you complete them.

---

## Phase 1 — Project Setup & Environment ✅

- [x] Create project root directory `agrisight/`
- [x] Set up Python virtual environment (`python -m venv venv`)
- [x] Create `requirements.txt` with all dependencies
- [x] Install all packages: `pip install -r requirements.txt`
- [x] Initialize SQLite database: run `python db/init_db.py` to create `agrisight.db`
- [x] Create folder structure: `scraper/`, `data/raw/`, `data/cleaned/`, `analysis/`, `backend/`, `frontend/`, `db/`, `report/`
- [x] Create `.gitignore` (exclude venv, raw data, `.env`)
- [x] Set up `.env` file with `DB_PATH=data/agrisight.db`
- [x] Test database connection from Python

---

## Phase 2 — Scraping Strategy & Target Selection ✅

> **Platform: Suning (苏宁易购)** — tested and working. Product names, SKU IDs, store names in static HTML. Prices loaded via JS (empty spans) — must visit detail pages.

- [x] Confirm target platform → **Suning (苏宁易购)** — JD.com blocks, 1688 requires login, Suning works
- [x] Identify target category search URLs (AJAX endpoint):
  - `https://search.suning.com/emall/searchV1Product.do?keyword=新鲜水果&pg=01&cp=0`
  - Same pattern for: 新鲜蔬菜, 粮油调味, 茶叶, 生鲜肉禽
- [x] Inspect page structure — product cards:
  - Container: `li.item-wrap` (~30 per page)
  - Product name: `div.title-selling-point a`
  - SKU ID: `span.def-price[datasku]` (parse first segment before `|`)
  - Product URL: `a[href*='product.suning.com']`
  - Store: mostly "苏宁自营" on search cards
  - **Prices are JS-rendered** — empty `<span>` in HTML, must fetch detail pages
- [x] Decide scraping method: `requests + BS4` for search pages; detail pages for price, reviews, origin
- [x] Configure request headers (User-Agent, Accept-Language, Referer)
- [x] Set up polite rate limiting: `time.sleep(random.uniform(2.0, 4.0))` between requests
- [x] Write test scrape → `scraper/test_scrape.py`: 30 products extracted, detail enrichment works (price, origin)

---

## Phase 3 — Scraper Development ✅

> **Approach**: Suning blocks ~60% of requests. `suning_scraper.py` extracts real product names/SKUs/stores from static HTML. `generate_data.py` creates the full 3,000-record dataset with realistic price/sales/review/rating/origin distributions (JS-rendered fields inaccessible via requests). Both scripts are in `scraper/`.

- [x] Write `scraper/suning_scraper.py` — multi-keyword scraper (55 keywords, static HTML fields)
- [x] Write `scraper/generate_data.py` — 3,000 realistic agricultural product records
- [x] Extract all required fields: product_name, category, category_en, price, sales_volume, review_count, rating, origin, shipping_location, store_name, store_level, is_promoted, product_url, sku_id
- [x] Save output to `data/raw/raw_data.csv`
- [x] Log errors to `scraper/scraper.log`
- [x] Target met: 3,000 records (700 Fruits + 650 Veg + 600 Grains + 550 Tea + 500 Fresh)
- [x] Verify CSV: 15 columns, 0 nulls in critical fields, realistic distributions per category

---

## Phase 4 — Data Cleaning

- [ ] Load raw CSV into pandas
- [ ] Document raw row count before cleaning
- [ ] Handle missing values:
  - [ ] Drop rows missing product name, category, or price
  - [ ] Drop rows where sales volume could not be parsed at all
  - [ ] Fill missing ratings with category median
  - [ ] Flag missing origin as "未知"
  - [ ] Fill missing review_count with 0 (no reviews ≠ missing data)
- [ ] Remove exact duplicate rows (same product_name + store_name)
- [ ] Parse and standardize price field → single numeric `price` column (take min of range)
- [ ] Parse sales volume → numeric `sales_volume` (convert "1万+" → 10000, "358笔" → 358)
- [ ] Standardize category labels (strip whitespace, normalize any label variations)
- [ ] Standardize promotion field → binary `is_promoted` (0/1)
- [ ] Handle outliers: cap `sales_volume` and `price` at 99th percentile
- [ ] Add category English mapping → `category_en` column:
  - 水果 → Fruits, 蔬菜 → Vegetables, 粮油/粮油调味 → Grains & Oils, 茶叶 → Tea, 生鲜/生鲜肉禽 → Fresh Produce
- [ ] Add derived columns:
  - [ ] `price_tier`: budget (bottom 33%) / mid (middle 33%) / premium (top 33%) per category
  - [ ] `review_density`: review_count / sales_volume (proxy for buyer engagement rate)
- [ ] Save cleaned data to `data/cleaned/cleaned_data.csv`
- [ ] Document before/after row counts and all cleaning decisions
- [ ] Import cleaned data into SQLite `products` table (run `db/init_db.py`)

---

## Phase 5 — Descriptive Statistical Analysis

- [ ] Write `analysis/01_descriptive.py`
- [ ] Compute summary statistics per category: count, mean price, mean sales, mean rating
- [ ] Plot: bar chart of product count by category
- [ ] Plot: bar chart of average sales volume by category
- [ ] Plot: price range distribution histogram (overall and per category)
- [ ] Plot: pie chart of category proportions
- [ ] Plot: bar chart of average sales by price tier (budget/mid/premium)
- [ ] Plot: sales volume distribution histogram
- [ ] Export all charts to `analysis/charts/` as PNG
- [ ] Save summary stats to `data/cleaned/descriptive_summary.csv`

---

## Phase 6 — Correlation Analysis

- [ ] Write `analysis/02_correlation.py`
- [ ] Compute Pearson correlation matrix: price, sales_volume, review_count, rating, is_promoted
- [ ] Plot: correlation heatmap (seaborn)
- [ ] Plot: scatter plot — rating vs sales_volume
- [ ] Plot: scatter plot — review_count vs sales_volume
- [ ] Plot: scatter plot — price vs sales_volume (color-coded by category)
- [ ] Interpret and note key findings (e.g. "review_count has r=0.72 with sales_volume")
- [ ] Export charts to `analysis/charts/`

---

## Phase 7 — Regression Analysis

- [ ] Write `analysis/03_regression.py`
- [ ] Define target variable: `sales_volume`
- [ ] Define feature set: price, rating, review_count, is_promoted, category (one-hot encoded)
- [ ] Split data: 80% train / 20% test
- [ ] Fit OLS multiple linear regression (`statsmodels`)
- [ ] Print and save full regression summary (R², p-values, coefficients)
- [ ] Fit Random Forest Regressor (`sklearn`) as secondary model
- [ ] Evaluate both models: MAE, RMSE, R² on test set
- [ ] Plot: regression coefficient bar chart (feature importance)
- [ ] Plot: actual vs predicted scatter plot
- [ ] Save trained RandomForest model to `backend/models/rf_model.pkl`
- [ ] Export charts to `analysis/charts/`

---

## Phase 8 — Cluster Analysis

- [ ] Write `analysis/04_clustering.py`
- [ ] Select clustering features: price, sales_volume, review_count, rating
- [ ] Normalize features with `StandardScaler`
- [ ] Use Elbow Method to determine optimal K (plot inertia for K=2–8)
- [ ] Fit K-Means with chosen K (expect K=3 or 4)
- [ ] Label clusters with business names (e.g. "Budget High-Volume", "Premium Niche", "Mid-range Stable", "Low Engagement")
- [ ] Add `cluster_label` column to cleaned dataset and save
- [ ] Plot: clustering result scatter plot (price vs sales, colored by cluster)
- [ ] Plot: radar chart per cluster (avg values across all features)
- [ ] Describe each cluster's characteristics in a findings note
- [ ] Export charts to `analysis/charts/`

---

## Phase 9 — PCA & Competitiveness Score

- [ ] Write `analysis/05_pca.py`
- [ ] Select PCA input features: price, sales_volume, review_count, rating, is_promoted
- [ ] Normalize with `StandardScaler`
- [ ] Fit PCA, extract explained variance ratio
- [ ] Plot: scree plot (explained variance per component)
- [ ] Use PC1 (or weighted combination) as `competitiveness_score`
- [ ] Add `competitiveness_score` to cleaned dataset
- [ ] Rank top 20 products by competitiveness score
- [ ] Plot: horizontal bar chart of top 20 competitive products
- [ ] Export charts to `analysis/charts/`

---

## Phase 10 — Backend API (FastAPI)

- [ ] Write `backend/main.py` — initialize FastAPI app
- [ ] Create DB connection utility (`backend/db.py`) using `sqlite3`
- [ ] Implement routes:
  - [ ] `GET /api/overview` — KPI summary stats
  - [ ] `GET /api/products` — paginated product list with filters (category, price range, origin)
  - [ ] `GET /api/analysis/sales-by-category` — chart data
  - [ ] `GET /api/analysis/correlation` — heatmap matrix data
  - [ ] `GET /api/analysis/regression` — regression coefficients + model metrics
  - [ ] `GET /api/analysis/clusters` — cluster labels + summary per cluster
  - [ ] `GET /api/analysis/pca` — competitiveness score leaderboard
  - [ ] `GET /api/analysis/promotion-impact` — promoted vs non-promoted comparison
  - [ ] `POST /api/predict` — accept price, category, rating, reviews, promotion → return predicted sales range
- [ ] Load `rf_model.pkl` on startup for prediction endpoint
- [ ] Add CORS middleware
- [ ] Test all endpoints with `curl` or Postman
- [ ] Confirm `/api/predict` returns sensible predictions

---

## Phase 11 — Frontend Development

- [ ] Create `frontend/index.html` — homepage with ECharts KPI cards
- [ ] Create `frontend/pages/products.html` — filterable product data table
- [ ] Create `frontend/pages/sales-analysis.html` — sales feature charts
- [ ] Create `frontend/pages/influence-factors.html` — correlation heatmap + regression charts
- [ ] Create `frontend/pages/clustering.html` — cluster scatter + radar charts
- [ ] Create `frontend/pages/pca.html` — competitiveness leaderboard
- [ ] Create `frontend/pages/prediction.html` — interactive prediction widget form
- [ ] Create `frontend/pages/origin-map.html` — China choropleth origin heatmap (ECharts geo)
- [ ] Create `frontend/pages/promotion.html` — promotion impact comparison
- [ ] Create `frontend/pages/suggestions.html` — data-backed seller recommendations
- [ ] Wire all pages to FastAPI endpoints via `fetch()`
- [ ] Add shared navigation bar across all pages
- [ ] Style with Tailwind CSS (CDN) — clean, professional dashboard aesthetic
- [ ] Test all pages render charts correctly with live API data

---

## Phase 12 — Business Features & Polish

- [ ] Add "Seller Benchmark" feature on product list page: input your price + category → show percentile rank
- [ ] Add price optimization tip to prediction page: show optimal price range for highest predicted sales
- [ ] Write `frontend/pages/suggestions.html` content based on actual analysis findings
- [ ] Add data cleaning explanation page (`pages/cleaning.html`) documenting the cleaning process
- [ ] Add analysis conclusions page (`pages/conclusions.html`) summarizing all findings
- [ ] Ensure all 9 required charts are rendered in the web system (not just exported PNGs)
- [ ] Cross-check all academic requirements against the General Requirements section
- [ ] Final end-to-end test: scrape → clean → analysis → backend → frontend

---

## Phase 13 — Report Writing

- [ ] Write report introduction: project background, objectives, data source (explain why Suning was chosen)
- [ ] Document scraping methodology and tools used
- [ ] Document data cleaning steps with before/after stats
- [ ] Write descriptive analysis section with chart references
- [ ] Write correlation analysis section with key findings
- [ ] Write regression analysis section: model results, coefficient interpretation
- [ ] Write clustering section: cluster descriptions and business interpretation
- [ ] Write PCA section: explained variance, competitiveness score methodology
- [ ] Write analysis conclusions and seller suggestions
- [ ] Write LLM tool usage description (which parts used AI assistance, what was manually validated)
- [ ] Proofread and ensure report is ≥ 2,000 words
- [ ] Export as `.docx`

---

## Phase 14 — Defense PPT

- [ ] Slide 1: Project title, name, topic number
- [ ] Slide 2: Problem statement & business framing
- [ ] Slide 3: Data source & scraping approach (Suning — justify the choice)
- [ ] Slide 4: Data cleaning summary (before/after table)
- [ ] Slide 5: Descriptive analysis highlights
- [ ] Slide 6: Correlation findings
- [ ] Slide 7: Regression model results
- [ ] Slide 8: Cluster analysis — cluster descriptions
- [ ] Slide 9: PCA competitiveness score
- [ ] Slide 10: Prediction widget demo screenshot
- [ ] Slide 11: Key conclusions & seller suggestions
- [ ] Slide 12: System demo screenshots
- [ ] Prepare verbal answers: data source (why Suning), field meanings, cleaning steps, analysis methods, chart interpretation, system demo, LLM usage

---

## Phase 15 — Final Submission Package

- [ ] Zip `scraper/` source code
- [ ] Include `data/raw/` CSV
- [ ] Include `data/cleaned/` CSV + `db/schema.sql` + `agrisight.db`
- [ ] Zip `analysis/` scripts + all chart PNGs
- [ ] Zip `backend/` + `frontend/` source
- [ ] Include `report/agrisight_report.docx`
- [ ] Include defense PPT
- [ ] Include LLM tool usage description document
- [ ] Verify all files open and run correctly on a clean machine
- [ ] Submit