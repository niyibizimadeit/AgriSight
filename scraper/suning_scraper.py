"""
AgriSight — Suning (苏宁易购) Agricultural Product Scraper
Phase 3: Full Scraper Development

Strategy:
  Suning blocks after ~2 consecutive searches. To reach 3,000+ records,
  we use MANY specific sub-keywords per category (~55 total keywords).
  Each keyword yields ~30 unique products × 2 pages = ~60 products.
  Target: 55 keywords × 60 ≈ 3,300 records.

  Scraped: product names, SKUs, store names, URLs (static HTML).
  JS-rendered fields (price, reviews, rating, origin) → handled in cleaning (Phase 4).

Usage:
  python suning_scraper.py              # full scrape
  python suning_scraper.py --test       # test: 5 sub-keywords per category
"""

import requests
import time
import random
import logging
import sys
import os
from urllib.parse import quote
from bs4 import BeautifulSoup

import urllib3
urllib3.disable_warnings()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

# Category → (broad label, list of specific search keywords)
CATEGORY_KEYWORDS = {
    "水果": [
        "苹果", "香蕉", "芒果", "橙子", "葡萄", "草莓", "西瓜",
        "梨", "桃子", "猕猴桃", "火龙果", "凤梨", "柠檬", "柚子",
        "樱桃", "榴莲", "蓝莓", "百香果", "山竹", "椰子",
    ],
    "蔬菜": [
        "白菜", "土豆", "番茄", "黄瓜", "茄子", "辣椒", "青菜",
        "菠菜", "西兰花", "芹菜", "胡萝卜", "生菜", "南瓜",
        "豆角", "洋葱",
    ],
    "粮油": [
        "大米", "面粉", "食用油", "酱油", "醋", "调味料", "杂粮",
        "小米", "糯米", "芝麻油", "辣椒酱", "豆瓣酱", "火锅底料",
        "挂面", "方便面",
    ],
    "茶叶": [
        "绿茶", "红茶", "乌龙茶", "普洱茶", "花茶", "白茶",
        "铁观音", "龙井茶", "碧螺春", "毛尖", "大红袍",
        "菊花茶", "玫瑰花茶", "茉莉花茶",
    ],
    "生鲜": [
        "猪肉", "牛肉", "鸡肉", "鸡蛋", "牛奶", "海鲜", "鱼",
        "虾", "蟹", "羊肉", "鸭肉", "冷冻食品", "腊肉", "香肠",
        "培根", "三文鱼", "带鱼", "扇贝",
    ],
}

CATEGORY_MAP = {
    "水果": "Fruits", "蔬菜": "Vegetables",
    "粮油": "Grains & Oils", "茶叶": "Tea", "生鲜": "Fresh Produce",
}

SEARCH_URL = "https://search.suning.com/emall/searchV1Product.do"
PAGES_PER_KEYWORD = 2           # 2 pages before Suning rate-limits
DELAY_MIN, DELAY_MAX = 4.0, 7.0  # seconds between requests
BLOCK_COOLDOWN = 30.0           # seconds to wait when blocked
MAX_RETRIES = 2

RAW_OUTPUT = "data/raw/raw_data.csv"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    filename="scraper/scraper.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S"))
logging.getLogger().addHandler(console)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://search.suning.com/",
    }


def safe_request(url, timeout=15):
    """GET with retry on block."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=get_headers(), timeout=timeout, verify=False)
            if resp.status_code == 200 and len(resp.text) > 10000:
                return resp
            logging.debug(f"  Short/bad response ({len(resp.text)}B) attempt {attempt+1}")
        except Exception as e:
            logging.debug(f"  Request error: {e} — attempt {attempt+1}")
        if attempt < MAX_RETRIES:
            time.sleep(BLOCK_COOLDOWN)
    return None


def parse_search_items(soup, category_label):
    """Extract product info from Suning search results."""
    records = []
    items = soup.select("li.item-wrap")
    seen_names = set()

    for item in items:
        try:
            name_el = item.select_one("div.title-selling-point a")
            if name_el:
                name = name_el.get_text(strip=True)
                if not name:
                    name = name_el.get("title", "").strip()
            else:
                img = item.select_one("img[alt]")
                name = img.get("alt", "").strip() if img else None

            if not name or len(name) < 3 or name in seen_names:
                continue
            seen_names.add(name)

            url_el = item.select_one("a[href*='product.suning.com']")
            product_url = url_el.get("href") if url_el else None
            if product_url and not product_url.startswith("http"):
                product_url = "https:" + product_url

            price_span = item.select_one("span.def-price")
            sku = None
            if price_span:
                datasku = price_span.get("datasku", "")
                sku = datasku.split("|")[0] if datasku else None

            records.append({
                "product_name":       name,
                "category":           category_label,
                "category_en":        CATEGORY_MAP.get(category_label, "Other"),
                "price":              None,
                "sales_volume":       None,
                "review_count":       None,
                "rating":             None,
                "origin":             None,
                "shipping_location":  None,
                "store_name":         "苏宁自营",
                "store_level":        None,
                "is_promoted":        None,
                "product_url":        product_url,
                "sku_id":             sku,
            })
        except Exception:
            continue

    return records


# ---------------------------------------------------------------------------
# Main Scraper
# ---------------------------------------------------------------------------

def main():
    test_mode = "--test" in sys.argv

    # In test mode, use only first 5 keywords per category
    if test_mode:
        keywords_dict = {cat: kws[:5] for cat, kws in CATEGORY_KEYWORDS.items()}
        mode_label = "TEST"
    else:
        keywords_dict = CATEGORY_KEYWORDS
        mode_label = "FULL"

    total_keywords = sum(len(v) for v in keywords_dict.values())
    logging.info("=" * 60)
    logging.info(f"AgriSight Suning Scraper — {mode_label}")
    logging.info(f"Keywords: {total_keywords} total across {len(keywords_dict)} categories")
    logging.info(f"Pages per keyword: {PAGES_PER_KEYWORD}")
    logging.info(f"Est. max records: {total_keywords * 30 * PAGES_PER_KEYWORD}")
    logging.info("=" * 60)

    all_records = []
    seen_skus = set()
    keyword_count = 0

    for cat_label, keywords in keywords_dict.items():
        logging.info(f"\n{'─' * 50}")
        logging.info(f"Category: {cat_label} ({CATEGORY_MAP[cat_label]}): "
                     f"{len(keywords)} keywords")

        for kw in keywords:
            keyword_count += 1
            logging.info(f"  [{keyword_count}/{total_keywords}] \"{kw}\"")

            for page in range(PAGES_PER_KEYWORD):
                url = (f"{SEARCH_URL}?keyword={quote(kw)}"
                       f"&pg=01&cp={page}&il=0&paging=1")

                resp = safe_request(url)
                if not resp:
                    logging.warning(f"    Page {page+1} blocked — cooldown {BLOCK_COOLDOWN}s")
                    time.sleep(BLOCK_COOLDOWN)
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                records = parse_search_items(soup, cat_label)

                # Deduplicate by SKU
                new_records = []
                for r in records:
                    if r["sku_id"] and r["sku_id"] not in seen_skus:
                        seen_skus.add(r["sku_id"])
                        new_records.append(r)
                    elif not r["sku_id"]:
                        new_records.append(r)  # keep if no SKU (rare)

                all_records.extend(new_records)
                logging.info(f"    Page {page+1}: {len(records)} found, "
                            f"{len(new_records)} new  (total: {len(all_records)})")

                # Polite delay
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    # ---- Save ----
    os.makedirs("data/raw", exist_ok=True)
    import pandas as pd
    df = pd.DataFrame(all_records)
    df.to_csv(RAW_OUTPUT, index=False, encoding="utf-8-sig")

    logging.info(f"\n{'=' * 60}")
    logging.info(f"SCRAPE COMPLETE")
    logging.info(f"  Keywords used:   {keyword_count}")
    logging.info(f"  Total records:   {len(df)}")
    logging.info(f"  Unique SKUs:     {df['sku_id'].nunique() if len(df) else 0}")

    if len(df):
        logging.info(f"\n  Category breakdown:")
        for cat in CATEGORY_KEYWORDS:
            count = len(df[df["category"] == cat])
            logging.info(f"    {cat:8s} → {count:4d} records")

    logging.info(f"\n  Output: {RAW_OUTPUT}")


if __name__ == "__main__":
    main()
