# ✅ AgriSight — TODO

All tasks organized by phase. Check off items as you complete them.

---

## Phase 1 — Project Setup & Environment

- [ ] Create project root directory `agrisight/`
- [ ] Set up Python virtual environment (`python -m venv venv`)
- [ ] Create `requirements.txt` with all dependencies
- [ ] Install all packages: `pip install -r requirements.txt`
- [ ] Initialize MySQL database and create `agrisight` schema
- [ ] Create folder structure: `scraper/`, `data/raw/`, `data/cleaned/`, `analysis/`, `backend/`, `frontend/`, `db/`, `report/`
- [ ] Create `.gitignore` (exclude venv, raw data, `.env`)
- [ ] Set up `.env` file for DB credentials and config
- [ ] Test database connection from Python

---

## Phase 2 — Scraping Strategy & Target Selection

- [ ] Choose primary target platform (JD.com recommended — more accessible than Taobao)
- [ ] Identify target category URLs for: 水果 (fruits), 蔬菜 (vegetables), 粮油 (grains & oils), 茶叶 (tea), 生鲜 (fresh produce)
- [ ] Inspect page structure (DevTools → Network tab) to identify data-carrying elements
- [ ] Decide on scraping method: `requests + BS4` for static pages, `Selenium` for JS-rendered pages
- [ ] Configure request headers (User-Agent rotation, cookies if needed)
- [ ] Set up polite rate limiting (1–3 second delays between requests)
- [ ] Write a test scrape of 20 records to validate field extraction

---

## Phase 3 — Scraper Development

- [ ] Write `jd_scraper.py` main scraper class
- [ ] Implement pagination logic (loop through page 1–N per category)
- [ ] Extract all required fields per product:
  - [ ] Product name
  - [ ] Category
  - [ ] Price (handle ranges like "¥12–¥45")
  - [ ] Sales volume (handle "1万+" format)
  - [ ] Review count
  - [ ] Rating (if available)
  - [ ] Origin / 产地
  - [ ] Shipping location
  - [ ] Store name
  - [ ] Promotion status (is there a discount/coupon flag?)
  - [ ] Product URL
- [ ] Save raw output to `data/raw/raw_YYYY-MM-DD.csv` after each run
- [ ] Log errors and skipped records to `scraper.log`
- [ ] Run full scrape targeting 2,000+ records
- [ ] Verify raw CSV column completeness and row count

---

## Phase 4 — Data Cleaning

- [ ] Load raw CSV into pandas
- [ ] Document raw row count before cleaning
- [ ] Handle missing values:
  - [ ] Drop rows missing product name, category, price, or sales volume
  - [ ] Fill missing ratings with category median
  - [ ] Flag missing origin as "未知"
- [ ] Remove exact duplicate rows
- [ ] Parse and standardize price field → single numeric `price` column
- [ ] Parse sales volume → numeric `sales_volume` (convert "1万+" → 10000)
- [ ] Standardize category labels (normalize variations, strip whitespace)
- [ ] Standardize promotion field → binary `is_promoted` (0/1)
- [ ] Handle outliers: cap sales_volume and price at 99th percentile
- [ ] Add derived columns: `price_tier` (budget/mid/premium), `review_density` (reviews/sales)
- [ ] Save cleaned data to `data/cleaned/cleaned_data.csv`
- [ ] Document before/after row counts and cleaning decisions
- [ ] Import cleaned data into MySQL `products` table

---

## Phase 5 — Descriptive Statistical Analysis

- [ ] Write `analysis/01_descriptive.py`
- [ ] Compute summary statistics per category: count, mean price, mean sales, mean rating
- [ ] Plot: bar chart of product count by category
- [ ] Plot: bar chart of average sales volume by category
- [ ] Plot: price range distribution histogram (overall and per category)
- [ ] Plot: pie chart of category proportions
- [ ] Plot: sales volume distribution histogram
- [ ] Export all charts to `analysis/charts/` as PNG
- [ ] Save summary stats to `data/cleaned/descriptive_summary.csv`

---

## Phase 6 — Correlation Analysis

- [ ] Write `analysis/02_correlation.py`
- [ ] Compute Pearson correlation matrix: price, sales_volume, review_count, rating, is_promoted
- [ ] Plot: correlation heatmap (seaborn or matplotlib)
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
- [ ] Save trained RandomForest model to `backend/models/rf_model.pkl` (for prediction API)
- [ ] Export charts to `analysis/charts/`

---

## Phase 8 — Cluster Analysis

- [ ] Write `analysis/04_clustering.py`
- [ ] Select clustering features: price, sales_volume, review_count, rating
- [ ] Normalize features with `StandardScaler`
- [ ] Use Elbow Method to determine optimal K (plot inertia for K=2–8)
- [ ] Fit K-Means with chosen K (expect K=3 or 4)
- [ ] Label clusters with business names (e.g. "Budget High-Volume", "Premium Niche", "Mid-range Stable")
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
- [ ] Create DB connection utility (`backend/db.py`) using `mysql-connector-python` or `SQLAlchemy`
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

- [ ] Write report introduction: project background, objectives, data source
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
- [ ] Slide 3: Data source & scraping approach
- [ ] Slide 4: Data cleaning summary (before/after table)
- [ ] Slide 5: Descriptive analysis highlights
- [ ] Slide 6: Correlation findings
- [ ] Slide 7: Regression model results
- [ ] Slide 8: Cluster analysis — cluster descriptions
- [ ] Slide 9: PCA competitiveness score
- [ ] Slide 10: Prediction widget demo screenshot
- [ ] Slide 11: Key conclusions & seller suggestions
- [ ] Slide 12: System demo screenshots
- [ ] Prepare verbal answers: data source, field meanings, cleaning steps, analysis methods, chart interpretation, system demo, LLM usage

---

## Phase 15 — Final Submission Package

- [ ] Zip `scraper/` source code
- [ ] Include `data/raw/` CSV
- [ ] Include `data/cleaned/` CSV + `db/schema.sql` + MySQL dump
- [ ] Zip `analysis/` scripts + all chart PNGs
- [ ] Zip `backend/` + `frontend/` source
- [ ] Include `report/agrisight_report.docx`
- [ ] Include defense PPT
- [ ] Include LLM tool usage description document
- [ ] Verify all files open and run correctly on a clean machine
- [ ] Submit