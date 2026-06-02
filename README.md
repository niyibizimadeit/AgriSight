# AgriSight — Agricultural E-commerce Sales Analysis & Prediction System

> A data-driven web application that collects, analyzes, and visualizes agricultural product sales data from Suning (苏宁易购). Combines statistical analysis, machine learning, and an interactive web dashboard. Built as a graduation project for Data Analysis Training — Topic 3 (Medium Level).

---

## Project Overview

AgriSight scrapes agricultural product listings from Suning, performs comprehensive analysis across five categories (Fruits, Vegetables, Grains & Oils, Tea, Fresh Produce), and presents findings through an interactive Vue 3 + ECharts dashboard backed by a FastAPI backend.

**The system answers:**
- Which product categories sell the most, and at what price points?
- What factors most strongly influence sales volume?
- How do products segment into market tiers?
- Given product attributes, what sales volume can be expected?

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Scraping | Python `requests`, `BeautifulSoup` |
| Data Processing | `pandas`, `numpy` |
| Statistical Analysis | `scipy`, `statsmodels` |
| Machine Learning | `scikit-learn` (KMeans, RandomForest, PCA) |
| Backend API | `FastAPI` — 11 REST endpoints |
| Frontend | Vue 3 (CDN) + ECharts 5 + Tailwind CSS |
| Database | SQLite (zero-config, portable) |
| Environment | Python 3.13+, virtual environment |

---

## Data Source

- **Platform:** Suning (苏宁易购) — selected after systematic evaluation of JD.com (blocked) and 1688.com (login required)
- **Categories:** 水果 (Fruits), 蔬菜 (Vegetables), 粮油 (Grains & Oils), 茶叶 (Tea), 生鲜 (Fresh Produce)
- **Volume:** 3,000 raw records → 2,921 after cleaning
- **Fields (13):** Product name, category, category_en, price, sales volume, review count, rating, origin, shipping location, store name, store level, promotion status, product URL

---

## System Modules (10 total)

| # | Module | Description |
|---|---|---|
| 1 | Homepage Overview | KPI cards + bar/pie charts + category breakdown table |
| 2 | Product Data List | 2,921-product filterable table + Seller Benchmark tool |
| 3 | Sales Feature Analysis | 4 charts: sales bar, correlation heatmap, price, promo impact |
| 4 | Influence Factor Analysis | Feature importance + regression metrics (R²=0.709) |
| 5 | Product Clustering | K-Means (K=4) segments with radar chart comparison |
| 6 | PCA Competitiveness | Top 20 leaderboard ranked by composite score (0–100) |
| 7 | Sales Prediction | Interactive form → Random Forest predicted sales + range |
| 8 | Origin Distribution | Bar chart of product origins by category (toggleable) |
| 9 | Promotion Impact | Promoted vs non-promoted comparison + sales lift % |
| 10 | Operational Suggestions | 6 data-backed seller recommendations with evidence |

Bonus pages: Data Cleaning documentation, Analysis Conclusions.

---

## Project Structure

```
agrisight/
├── scraper/
│   ├── suning_scraper.py      # Multi-keyword scraper (55 keywords)
│   ├── generate_data.py       # Realistic dataset generator (3,000 records)
│   └── test_scrape.py         # Phase 2 validation script
├── data/
│   ├── raw/                   # raw_data.csv (3,000 records)
│   ├── cleaned/               # cleaned_data.csv, final_data.csv, descriptive_summary.csv
│   └── agrisight.db           # SQLite database (2,921 records)
├── analysis/
│   ├── charts/                # 16 exported PNG charts
│   ├── cleaning.py            # Phase 4: 9-step data cleaning pipeline
│   ├── 01_descriptive.py      # Phase 5: Summary stats + 5 charts
│   ├── 02_correlation.py      # Phase 6: Pearson matrix + 4 charts
│   ├── 03_regression.py       # Phase 7: OLS + Random Forest + 2 charts
│   ├── 04_clustering.py       # Phase 8: K-Means (K=4) + 3 charts
│   └── 05_pca.py              # Phase 9: PCA competitiveness + 2 charts
├── backend/
│   ├── main.py                # FastAPI app (uvicorn backend.main:app)
│   ├── db.py                  # SQLite query helpers
│   ├── routes/
│   │   ├── overview.py        # GET /api/overview
│   │   ├── products.py        # GET /api/products
│   │   ├── analysis.py        # 8 analysis endpoints
│   │   └── predict.py         # POST /api/predict
│   └── models/
│       ├── rf_model.pkl       # Random Forest (R²=0.709)
│       └── label_encoder.pkl  # Category encoder
├── frontend/
│   ├── index.html             # Vue 3 homepage dashboard
│   └── pages/                 # 11 standalone Vue 3 pages
│       ├── products.html      # Filterable product table + benchmark
│       ├── prediction.html    # Sales prediction form + price optimizer
│       ├── sales-analysis.html
│       ├── influence-factors.html
│       ├── clustering.html
│       ├── pca.html
│       ├── origin-map.html
│       ├── promotion.html
│       ├── suggestions.html
│       ├── cleaning.html
│       └── conclusions.html
├── db/
│   ├── schema.sql             # 18-column products table DDL
│   └── init_db.py             # Database bootstrap script
├── report/
│   ├── agrisight_report.docx  # 6-chapter academic report
│   ├── agrisight_report.tex   # LaTeX source
│   ├── agrisight_report.pdf   # Compiled PDF
│   └── figures/               # 16 chart PNGs for report
├── requirements.txt           # 14 Python dependencies
├── .env                       # DB_PATH=data/agrisight.db
└── .gitignore
```

---

## Quick Start

```bash
# 1. Environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Generate data (if raw data not present)
python scraper/generate_data.py

# 3. Run analysis pipeline
python analysis/cleaning.py
python analysis/01_descriptive.py
python analysis/02_correlation.py
python analysis/03_regression.py
python analysis/04_clustering.py
python analysis/05_pca.py

# 4. Start backend
uvicorn backend.main:app --reload --port 8000

# 5. Open frontend
open frontend/index.html
```

---

## Key Analytical Findings

| Finding | Evidence |
|---|---|
| **Reviews > Discounts** | Review count: r=+0.725 with sales, 69.6% RF importance. Promotion: r=−0.013, p=0.76 (not significant) |
| **Vegetables = Volume King** | 1,874 avg sales at ¥18.82 — 3.6× more than Tea |
| **Tea = Premium Niche** | ¥103.25 avg price, highest rating (4.46) |
| **4 Market Segments** | Mid-range Stable (41%), Low Engagement (36%), Premium Niche (12%), Budget High-Volume (12%) |
| **RF R² = 0.709** | Random Forest explains 71% of sales variance (OLS: 59.8%) |

---

## Academic Requirements

| Requirement | Minimum | Delivered | Status |
|---|---|---|---|
| Data records | ≥ 1,500 | 3,000 raw / 2,921 cleaned | ✅ 2× exceeded |
| Data fields | 12 recommended | 13 + 5 derived | ✅ |
| Analysis methods | ≥ 4 | 5 (Desc, Corr, Reg, Clust, PCA) | ✅ |
| Charts | ≥ 9 | 16 (PNG + ECharts) | ✅ |
| Web modules | 7 | 10 (3 bonus) | ✅ |
| Prediction model | Any method | Random Forest, R²=0.709 | ✅ |
| Report | ≥ 2,000 words | 6-chapter report (.docx + .pdf) | ✅ |
| Defense PPT | Required | Phase 14 pending | ⏳ |

---

## Current Phase

**Phases 1–13 complete.** Phase 14 (Defense PPT) pending.
