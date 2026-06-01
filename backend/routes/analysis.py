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


@router.get("/benchmark")
def seller_benchmark(category: str, price: float):
    """Compare a seller's price against competitors in the same category."""
    rows = query(
        "SELECT price FROM products WHERE category = ? AND price > 0",
        (category,),
    )
    if not rows:
        return {"error": "No data for this category"}

    prices = sorted([r["price"] for r in rows])
    n = len(prices)
    rank = sum(1 for p in prices if p < price)
    percentile = round(rank / n * 100, 1)

    return {
        "category": category,
        "your_price": price,
        "total_products": n,
        "percentile": percentile,
        "interpretation": (
            f"Your price is higher than {percentile}% of competitors"
            if percentile > 50
            else f"Your price is lower than {100 - percentile}% of competitors"
        ),
        "median_price": round(prices[n // 2], 2),
        "price_range": {
            "min": round(prices[0], 2),
            "p25": round(prices[n // 4], 2),
            "p75": round(prices[3 * n // 4], 2),
            "max": round(prices[-1], 2),
        },
    }


@router.get("/price-optimum")
def price_optimum(category: str):
    """Find the price range with the highest median sales in a category."""
    import pandas as pd
    import sqlite3
    from backend.db import get_connection

    conn = get_connection()
    df = pd.read_sql(
        "SELECT price, sales_volume FROM products WHERE category = ?",
        conn, params=(category,),
    )
    conn.close()

    if df.empty:
        return {"error": "No data for this category"}

    # Bin prices into ranges and find the best-performing range
    df["price_bin"] = pd.cut(df["price"], bins=5)
    bin_stats = df.groupby("price_bin", observed=False).agg(
        count=("price", "count"),
        avg_sales=("sales_volume", "mean"),
        median_sales=("sales_volume", "median"),
    ).round(0)
    best_bin = bin_stats["avg_sales"].idxmax()

    return {
        "category": category,
        "optimal_range": {
            "low": round(best_bin.left, 0),
            "high": round(best_bin.right, 0),
        },
        "avg_sales_in_range": int(bin_stats.loc[best_bin, "avg_sales"]),
        "product_count": int(bin_stats.loc[best_bin, "count"]),
        "all_bins": [
            {
                "range": f"¥{int(b.left)}–{int(b.right)}",
                "count": int(r["count"]),
                "avg_sales": int(r["avg_sales"]),
            }
            for b, r in bin_stats.iterrows()
        ],
    }
