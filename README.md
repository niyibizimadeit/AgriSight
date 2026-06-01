# AgriSight — Agricultural E-commerce Sales Analysis & Prediction System

> A market intelligence platform for agricultural product sellers, built on scraped e-commerce data from Chinese platforms. Combines statistical analysis, machine learning, and an interactive web dashboard to surface actionable pricing and sales insights.

---

## Project Overview

AgriSight is a data-driven web application that collects, cleans, analyzes, and visualizes agricultural product sales data from public e-commerce platforms (JD.com / Taobao). It is designed as both a **graduation project deliverable** (data analysis training — Topic 3, medium difficulty) and a **realistic B2B market intelligence tool** for agricultural sellers who want to understand pricing dynamics, competition, and demand patterns.

The system answers questions like:
- Which product categories sell the most, and at what price points?
- Does promotion status significantly lift sales volume?
- Which origin regions dominate which categories?
- Given my product's attributes, what sales volume can I expect?

---

## Business Framing

Rather than presenting this as a student analysis exercise, AgriSight is framed as a **Seller Intelligence Dashboard** — a tool an agricultural merchant would realistically pay to use. Key value propositions:

- **Benchmark your product** against competitors in the same category and price range
- **Predict expected sales** before setting a price
- **Understand what drives sales** through transparent regression and factor analysis
- **Discover underserved niches** via cluster analysis (high-rating, low-competition segments)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Scraping | Python `requests`, `Selenium`, `BeautifulSoup` |
| Data Processing | `pandas`, `numpy`, `regex` |
| Statistical Analysis | `scipy`, `statsmodels` |
| Machine Learning | `scikit-learn` (KMeans, RandomForest, PCA, LinearRegression) |
| Backend API | `FastAPI` |
| Frontend | HTML5 + ECharts + Tailwind CSS |
| Database | SQLite (zero-config, portable) |
| Environment | Python 3.10+, virtual environment |

---

## Data Source

- **Primary:** JD.com agricultural product category pages (`生鲜`, `粮油`, `茶叶`, `水果`, `蔬菜`)
- **Target volume:** 2,000+ raw records → 1,500+ after cleaning
- **Key fields:** Product name, category, price, sales volume, review count, rating, origin, shipping location, store name, promotion status

---

## System Modules

| Module | Description |
|---|---|
| Homepage Overview | KPI cards: total products, avg price, top category, total sales |
| Product Data List | Filterable/sortable table with full product info |
| Sales Feature Analysis | Sales by category, price range distribution |
| Influence Factor Analysis | Correlation heatmap, regression result charts |
| Product Clustering | K-Means tiers with radar charts per cluster |
| PCA Competitiveness Score | Ranked product leaderboard by composite score |
| Sales Prediction Widget | Interactive form → RandomForest predicted sales range |
| Origin Heatmap | China choropleth map of product origins by category |
| Promotion Impact Analysis | Promoted vs non-promoted sales lift comparison |
| Operational Suggestions | Data-backed seller recommendations |

---

## Deliverables Checklist

- [ ] Scraping source code
- [ ] Raw data CSV
- [ ] Cleaned data CSV + SQLite database file
- [ ] Analysis notebooks / scripts
- [ ] FastAPI backend source
- [ ] Frontend source (HTML + JS)
- [ ] All 9+ required charts (exported as PNG + rendered in web)
- [ ] Analysis report (≥ 2,000 words)
- [ ] Defense PPT
- [ ] LLM tool usage description

---

## Project Structure

```
agrisight/
├── scraper/
│   └── jd_scraper.py          # Main scraping script
├── data/
│   ├── raw/                   # Raw scraped CSV files
│   └── cleaned/               # Cleaned and processed data
├── analysis/
│   ├── charts/                # Exported PNG charts
│   ├── 01_descriptive.py
│   ├── 02_correlation.py
│   ├── 03_regression.py
│   ├── 04_clustering.py
│   └── 05_pca.py
├── backend/
│   ├── main.py                # FastAPI app entry point
│   ├── db.py                  # SQLite connection utility
│   ├── routes/
│   └── models/
├── frontend/
│   ├── index.html
│   ├── pages/
│   └── static/
├── db/
│   ├── schema.sql             # Reference DDL
│   ├── init_db.py             # Database initialization script
│   └── agrisight.db           # SQLite database file (auto-created)
├── report/
│   └── agrisight_report.docx
└── requirements.txt
```

---

## Academic Requirements Met

| Requirement | Status |
|---|---|
| ≥ 1,500 data records | Targeting 2,000 raw / 1,500 clean |
| ≥ 4 analysis methods | Descriptive, Correlation, Regression, Clustering, PCA (5 total) |
| Web system with all required modules | ✅ All 7 required + 3 bonus modules |
| ≥ 9 required charts | ✅ 9 required + origin heatmap + radar charts |
| Report ≥ 2,000 words | Planned |
| Defense PPT | Planned |
