-- AgriSight Database Schema (SQLite)
-- Reference DDL -- tables are created via db/init_db.py

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
