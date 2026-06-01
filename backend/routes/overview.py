"""GET /api/overview — KPI summary stats."""

from fastapi import APIRouter
from backend.db import query_one, query

router = APIRouter()


@router.get("/overview")
def overview():
    # Total counts
    total_products = query_one("SELECT COUNT(*) AS n FROM products")["n"]
    avg_price = query_one("SELECT AVG(price) AS v FROM products")["v"]
    total_sales = query_one("SELECT SUM(sales_volume) AS v FROM products")["v"]
    avg_rating = query_one("SELECT AVG(rating) AS v FROM products")["v"]
    promo_rate = query_one(
        "SELECT AVG(is_promoted) AS v FROM products"
    )["v"]

    # Top category by count
    top_cat = query_one(
        "SELECT category, COUNT(*) AS n FROM products "
        "GROUP BY category ORDER BY n DESC LIMIT 1"
    )

    # Category breakdown
    categories = query(
        "SELECT category, category_en, COUNT(*) AS count, "
        "AVG(price) AS avg_price, AVG(sales_volume) AS avg_sales, "
        "AVG(rating) AS avg_rating "
        "FROM products GROUP BY category, category_en ORDER BY count DESC"
    )

    return {
        "total_products": total_products,
        "avg_price": round(avg_price, 2) if avg_price else 0,
        "total_sales_volume": int(total_sales) if total_sales else 0,
        "avg_rating": round(avg_rating, 2) if avg_rating else 0,
        "promotion_rate": round(promo_rate * 100, 1) if promo_rate else 0,
        "top_category": top_cat,
        "categories": categories,
    }
