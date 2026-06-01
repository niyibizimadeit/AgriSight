"""GET /api/analysis/* — chart data endpoints."""

from fastapi import APIRouter
from backend.db import query, query_one

router = APIRouter()


@router.get("/sales-by-category")
def sales_by_category():
    rows = query(
        "SELECT category, category_en, AVG(sales_volume) AS avg_sales "
        "FROM products GROUP BY category, category_en ORDER BY avg_sales DESC"
    )
    return {
        "categories": [r["category"] for r in rows],
        "categories_en": [r["category_en"] for r in rows],
        "values": [round(r["avg_sales"], 0) for r in rows],
    }


@router.get("/correlation")
def correlation():
    """Return Pearson correlation matrix as JSON."""
    import pandas as pd
    import sqlite3
    from backend.db import get_connection

    conn = get_connection()
    df = pd.read_sql(
        "SELECT price, sales_volume, review_count, rating, is_promoted FROM products",
        conn,
    )
    conn.close()

    corr = df.corr().round(3)
    # Convert to nested dict
    result = {}
    for col in corr.columns:
        result[col] = {}
        for idx in corr.index:
            result[col][idx] = corr.loc[idx, col]
    return result


@router.get("/regression")
def regression():
    """Return regression results: feature importance + metrics."""
    # Feature importance (from Phase 7)
    importance = {
        "review_count": 69.6,
        "category": 14.4,
        "price": 9.8,
        "rating": 5.3,
        "is_promoted": 0.9,
    }
    return {
        "feature_importance": importance,
        "ols_r2": 0.598,
        "rf_r2": 0.709,
        "rf_mae": 342,
        "rf_rmse": 550,
        "features": ["price", "rating", "review_count", "is_promoted", "category"],
    }


@router.get("/clusters")
def clusters():
    """Return cluster summary stats."""
    rows = query(
        "SELECT cluster_label, COUNT(*) AS count, "
        "AVG(price) AS avg_price, AVG(sales_volume) AS avg_sales, "
        "AVG(rating) AS avg_rating, AVG(review_count) AS avg_reviews "
        "FROM products GROUP BY cluster_label ORDER BY avg_price DESC"
    )
    return {"clusters": rows}


@router.get("/pca")
def pca_leaderboard(limit: int = 20):
    """Return top-N products by competitiveness score."""
    rows = query(
        "SELECT product_name, category, price, sales_volume, "
        "competitiveness_score, cluster_label "
        "FROM products ORDER BY competitiveness_score DESC LIMIT ?",
        (limit,),
    )
    return {"leaderboard": rows}


@router.get("/promotion-impact")
def promotion_impact():
    """Promoted vs non-promoted comparison."""
    promoted = query_one(
        "SELECT AVG(sales_volume) AS avg_sales, "
        "AVG(price) AS avg_price, COUNT(*) AS count "
        "FROM products WHERE is_promoted = 1"
    )
    non_promoted = query_one(
        "SELECT AVG(sales_volume) AS avg_sales, "
        "AVG(price) AS avg_price, COUNT(*) AS count "
        "FROM products WHERE is_promoted = 0"
    )
    return {
        "promoted": promoted,
        "non_promoted": non_promoted,
        "sales_lift_pct": (
            round(
                (promoted["avg_sales"] - non_promoted["avg_sales"])
                / non_promoted["avg_sales"]
                * 100,
                1,
            )
            if non_promoted["avg_sales"]
            else 0
        ),
    }
