"""GET /api/products — paginated product list with filters."""

from fastapi import APIRouter, Query
from backend.db import query, query_one

router = APIRouter()


@router.get("/products")
def products(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    category: str = Query(None),
    price_min: float = Query(None),
    price_max: float = Query(None),
    origin: str = Query(None),
    sort_by: str = Query("id"),
):
    conditions = []
    params = {}

    if category:
        conditions.append("category = :category")
        params["category"] = category
    if price_min is not None:
        conditions.append("price >= :price_min")
        params["price_min"] = price_min
    if price_max is not None:
        conditions.append("price <= :price_max")
        params["price_max"] = price_max
    if origin:
        conditions.append("origin = :origin")
        params["origin"] = origin

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # Allowed sort columns
    sort_cols = {
        "id": "id", "price": "price", "sales": "sales_volume",
        "rating": "rating", "reviews": "review_count",
        "name": "product_name",
    }
    order_col = sort_cols.get(sort_by, "id")

    # Total count
    total = query_one(f"SELECT COUNT(*) AS n FROM products {where}", params)["n"]

    # Paginated results
    offset = (page - 1) * limit
    rows = query(
        f"SELECT * FROM products {where} ORDER BY {order_col} "
        f"LIMIT :limit OFFSET :offset",
        {**params, "limit": limit, "offset": offset},
    )

    # Distinct filter options
    categories = query("SELECT DISTINCT category FROM products ORDER BY category")
    origins = query(
        "SELECT DISTINCT origin FROM products "
        "WHERE origin != '未知' ORDER BY origin"
    )

    return {
        "items": rows,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "filters": {
            "categories": [c["category"] for c in categories],
            "origins": [o["origin"] for o in origins],
        },
    }
