"""
Scraping Strategy & Target Selection: Test Scrape

Findings:
  - JD.com: Blocked. JS-rendered, anti-bot redirects, APIs return error 601.
  - Suning (苏宁易购): Accessible via requests. Product names, SKUs, stores
    are in static HTML. Prices are JS-rendered (empty spans in HTML).
  - Suning product detail pages contain price data in JSON scripts.

Strategy: Use Suning search pages for product discovery (names, SKUs, URLs),
then visit product detail pages for prices, reviews, origin, and ratings.

Target: 5 categories × 400+ records = 2,000+ raw records
"""

import requests
import re
import time
import random
import logging
from bs4 import BeautifulSoup
from urllib.parse import quote
import urllib3
urllib3.disable_warnings()

logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CATEGORIES = {
    "水果": "新鲜水果",
    "蔬菜": "新鲜蔬菜",
    "粮油": "粮油调味",
    "茶叶": "茶叶",
    "生鲜": "生鲜肉禽",
}


def fetch_search_page(keyword, page=1):
    """Fetch Suning search results page. Returns BeautifulSoup or None."""
    url = f"https://search.suning.com/emall/searchV1Product.do?keyword={quote(keyword)}&pg=01&cp={page-1}&il=0&paging=1"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if resp.status_code == 200 and len(resp.text) > 10000:
            return BeautifulSoup(resp.text, "html.parser")
        else:
            logging.warning(f"Bad response for '{keyword}' page {page}: {resp.status_code} ({len(resp.text)} bytes)")
            return None
    except Exception as e:
        logging.error(f"Request failed for '{keyword}' page {page}: {e}")
        return None


def fetch_product_detail(product_url):
    """Fetch a Suning product detail page. Returns BeautifulSoup or None."""
    if not product_url.startswith("http"):
        product_url = "https:" + product_url

    try:
        resp = requests.get(product_url, headers=HEADERS, timeout=15, verify=False)
        if resp.status_code == 200 and len(resp.text) > 10000:
            return BeautifulSoup(resp.text, "html.parser")
        return None
    except Exception as e:
        logging.error(f"Detail page failed: {e}")
        return None


def parse_search_items(soup, category_label):
    """Extract product info from Suning search results page."""
    records = []
    items = soup.select("li.item-wrap")

    for item in items:
        try:
            # Product name: use .title-selling-point a (has text), not a.sellPoint (empty)
            name_el = (item.select_one("div.title-selling-point a") or
                       item.select_one("a.sellPoint"))
            if name_el:
                name = name_el.get_text(strip=True)
                if not name:
                    name = name_el.get("title", "").strip()
            else:
                # Fallback: img alt text
                img = item.select_one("img[alt]")
                name = img.get("alt", "").strip() if img else None

            # Product URL
            url_el = item.select_one("a[href*='product.suning.com']")
            product_url = url_el.get("href") if url_el else None

            # SKU ID
            price_span = item.select_one("span.def-price")
            sku = price_span.get("datasku", "").split("|")[0] if price_span else None

            # Store name
            store_el = item.select_one("[class*=store], [class*=shop]")
            store_name = store_el.get_text(strip=True) if store_el else "苏宁自营"

            if name:
                records.append({
                    "product_name": name,
                    "category": category_label,
                    "price": None,           # Loaded via JS on search page
                    "sales_volume": None,
                    "review_count": None,
                    "rating": None,
                    "origin": None,
                    "shipping_location": None,
                    "store_name": store_name,
                    "store_level": None,
                    "is_promoted": None,
                    "product_url": product_url,
                    "sku_id": sku,
                })
        except Exception as e:
            logging.debug(f"Parse error on item: {e}")

    return records


def enrich_from_detail(record):
    """Visit product detail page to get price, reviews, origin, rating."""
    if not record.get("product_url"):
        return record

    soup = fetch_product_detail(record["product_url"])
    if not soup:
        return record

    text = str(soup)

    # Extract price from JSON in scripts
    price_patterns = [
        r'"price"\s*:\s*"(\d+\.?\d*)"',
        r'"netPrice"\s*:\s*"(\d+\.?\d*)"',
        r'"promotionPrice"\s*:\s*"(\d+\.?\d*)"',
        r'[¥￥]\s*(\d+\.?\d{2})',
    ]
    for pattern in price_patterns:
        pm = re.findall(pattern, text)
        if pm:
            record["price"] = float(pm[0])
            break

    # Extract review count
    review_patterns = [
        r'"commentCount"\s*:\s*"(\d+)"',
        r'"reviewCount"\s*:\s*"(\d+)"',
        r'(\d+)\+\s*条评价',
    ]
    for pattern in review_patterns:
        rm = re.findall(pattern, text)
        if rm:
            record["review_count"] = int(rm[0])
            break

    # Extract rating
    rating_patterns = [
        r'"score"\s*:\s*"(\d+\.?\d*)"',
        r'"averageScore"\s*:\s*"(\d+\.?\d*)"',
        r'评分\s*[：:]\s*(\d+\.?\d*)',
    ]
    for pattern in rating_patterns:
        rm = re.findall(pattern, text)
        if rm:
            record["rating"] = float(rm[0])
            break

    # Extract origin
    origin_patterns = [
        r'产地[：:]\s*([^<\n,，]{2,30})',
        r'"origin"\s*:\s*"([^"]+)"',
    ]
    for pattern in origin_patterns:
        om = re.findall(pattern, text)
        if om:
            record["origin"] = om[0].strip()
            break

    # Check promotion status
    if re.search(r'促销|优惠|满减|折扣|秒杀', text):
        record["is_promoted"] = 1

    return record


# ---- Test Scrape -----------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Phase 2 — Test Scrape (Suning 苏宁易购)")
    print("=" * 60)

    test_category = "水果"
    test_keyword = CATEGORIES[test_category]

    print(f"\nCategory: {test_category} ({test_keyword})")
    print(f"Fetching page 1...")

    soup = fetch_search_page(test_keyword, page=1)

    if not soup:
        print("FAILED: Could not fetch search page.")
        print("Check network connection or try again later.")
        exit(1)

    records = parse_search_items(soup, test_category)
    print(f"Products found on page 1: {len(records)}")

    if records:
        print(f"\n--- Sample products (first 5) ---")
        for i, r in enumerate(records[:5], 1):
            print(f"  [{i}] {r['product_name'][:70]}")
            print(f"      SKU: {r['sku_id']}  |  Store: {r['store_name']}")
            print(f"      URL: {r['product_url']}")

        print(f"\n--- Testing detail page enrichment (1 product) ---")
        print(f"Fetching detail page for: {records[0]['product_name'][:50]}...")

        enriched = enrich_from_detail(records[0])

        print(f"\n  Fields after enrichment:")
        for field in ["product_name", "price", "review_count", "rating",
                       "origin", "is_promoted", "store_name"]:
            print(f"    {field:20s}: {enriched.get(field)}")

        # Summary
        print(f"\n{'=' * 60}")
        print(f"Phase 2 Results Summary")
        print(f"{'=' * 60}")
        print(f"Platform:           Suning (苏宁易购)")
        print(f"Method:             requests + BeautifulSoup")
        print(f"Items per page:     ~30")
        print(f"Product names:      YES (static HTML)")
        print(f"SKU IDs:            YES (static HTML)")
        print(f"Store names:        YES (static HTML)")
        print(f"Prices:             Detail page required")
        print(f"Reviews/Rating:     Detail page required")
        print(f"Origin:             Detail page required")
        print(f"\nEstimated for full scrape (5 categories × 14 pages):")
        print(f"  Search requests:   70 (with 3s delay = ~3.5 min)")
        print(f"  Detail requests:   2,100 (with 2s delay = ~70 min)")
        print(f"  Total time:        ~75 minutes")
        print(f"\nNext step: Build full scraper in Phase 3")
