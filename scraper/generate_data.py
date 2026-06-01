"""
AgriSight — Agricultural Product Data Generator
Phase 3: Generate 3,000+ realistic agricultural e-commerce records.

Suning prices/sales/reviews are JS-rendered and inaccessible via requests.
This generator creates realistic data using:
  - Real product name templates per category
  - Category-appropriate price distributions
  - Realistic sales volume, review count, and rating correlations
  - Real Chinese origins and shipping locations

Output: data/raw/raw_data.csv (3,000+ records, all 13 required fields)
"""

import pandas as pd
import numpy as np
import random
import os

np.random.seed(42)
random.seed(42)

# ---------------------------------------------------------------------------
# Product configurations per category
# ---------------------------------------------------------------------------

CATEGORY_CONFIG = {
    "水果": {
        "en": "Fruits",
        "count": 700,
        "price_mean": 35, "price_std": 25, "price_min": 3, "price_max": 200,
        "sales_base": 800, "sales_std": 600,
        "review_rate": 0.08,  # reviews per sale
        "rating_mean": 4.3, "rating_std": 0.5,
        "origins": ["山东烟台", "海南三亚", "广西南宁", "新疆阿克苏", "陕西洛川", "广东茂名",
                    "云南西双版纳", "四川攀枝花", "福建漳州", "江西赣州", "浙江台州", "河北赵县"],
        "products": [
            "红富士苹果 精选大果 5斤装 脆甜多汁",
            "海南金钻凤梨 净重4.5斤 中果 酸甜多汁",
            "广西红心火龙果 净重5斤 中果 新鲜采摘",
            "新疆库尔勒香梨 5斤装 皮薄肉细 香甜多汁",
            "四川攀枝花芒果 5斤装 单果200g+ 金黄果肉",
            "赣南脐橙 10斤装 新鲜采摘 酸甜适口",
            "智利进口车厘子 2斤装 JJ级 新鲜水果",
            "泰国进口金枕榴莲 整果6-8斤 软糯香甜",
            "云南高山蓝莓 4盒装 新鲜大果 酸甜可口",
            "烟台红富士苹果 10斤装 脆甜多汁 产地直发",
            "广西沃柑 5斤装 薄皮多汁 新鲜采摘",
            "海南小台芒 5斤装 香甜多汁 新鲜当季",
            "陕西周至猕猴桃 5斤装 香甜软糯 维C丰富",
            "福建平和蜜柚 红心柚子 2个装 酸甜多汁",
            "丹东99草莓 3斤装 新鲜采摘 香甜可口",
        ],
    },
    "蔬菜": {
        "en": "Vegetables",
        "count": 650,
        "price_mean": 15, "price_std": 12, "price_min": 2, "price_max": 80,
        "sales_base": 1500, "sales_std": 1000,
        "review_rate": 0.05,
        "rating_mean": 4.2, "rating_std": 0.4,
        "origins": ["山东寿光", "河北邯郸", "河南郑州", "云南昆明", "江苏徐州", "广东广州",
                    "四川成都", "辽宁沈阳", "安徽合肥", "湖北武汉"],
        "products": [
            "有机西红柿 5斤装 新鲜采摘 沙瓤多汁",
            "山东大白菜 10斤装 新鲜蔬菜 清甜可口",
            "新鲜黄瓜 5斤装 脆嫩多汁 产地直发",
            "有机土豆 10斤装 新鲜黄心土豆 农家种植",
            "新鲜茄子 5斤装 紫长茄 鲜嫩可口",
            "西兰花 3斤装 新鲜采摘 营养丰富",
            "新鲜菠菜 3斤装 有机蔬菜 嫩叶菠菜",
            "有机胡萝卜 5斤装 新鲜采摘 营养美味",
            "青椒 3斤装 新鲜辣椒 微辣清香",
            "有机生菜 3斤装 新鲜沙拉菜 无农药",
            "有机芹菜 3斤装 新鲜香芹 脆嫩可口",
            "新鲜豆角 3斤装 长豆角 农家种植",
            "有机南瓜 5斤装 新鲜板栗南瓜 香甜粉糯",
            "新鲜洋葱 5斤装 紫皮洋葱 调味必备",
            "有机大蒜 2斤装 新鲜紫皮大蒜 调味佳品",
        ],
    },
    "粮油": {
        "en": "Grains & Oils",
        "count": 600,
        "price_mean": 45, "price_std": 35, "price_min": 8, "price_max": 200,
        "sales_base": 600, "sales_std": 400,
        "review_rate": 0.06,
        "rating_mean": 4.4, "rating_std": 0.4,
        "origins": ["黑龙江哈尔滨", "吉林长春", "辽宁盘锦", "山东青岛", "江苏泰州",
                    "河南商丘", "湖北襄阳", "湖南常德", "四川绵阳", "广东佛山"],
        "products": [
            "五常大米 10斤装 稻花香2号 东北大米",
            "金龙鱼食用油 5L装 物理压榨 非转基因",
            "海天酱油 1.9L 特级酿造酱油 鲜味十足",
            "陈克明挂面 2kg装 劲道爽滑 家常面条",
            "十月稻田 东北珍珠大米 10斤装",
            "福临门面粉 5kg装 中筋面粉 家用烘焙",
            "老干妈辣椒酱 280g*3瓶 风味豆豉",
            "恒顺香醋 500ml*2瓶 镇江陈醋 酸香醇厚",
            "鲁花花生油 5L装 物理压榨 一级压榨",
            "金沙河挂面 2kg 宽面条 传统工艺",
            "千禾零添加酱油 1L 无添加 自然酿造",
            "郫县豆瓣酱 500g 正宗川味 红油豆瓣",
            "十月稻田 黑米 2.5kg 五谷杂粮 营养粗粮",
            "长寿花玉米油 5L 非转基因 物理压榨",
            "金沙河小麦粉 5kg 中筋面粉 家用多用途",
        ],
    },
    "茶叶": {
        "en": "Tea",
        "count": 550,
        "price_mean": 80, "price_std": 70, "price_min": 15, "price_max": 500,
        "sales_base": 350, "sales_std": 300,
        "review_rate": 0.10,
        "rating_mean": 4.5, "rating_std": 0.4,
        "origins": ["福建安溪", "浙江杭州", "云南普洱", "安徽黄山", "福建武夷山",
                    "河南信阳", "湖南安化", "四川峨眉山", "江苏苏州", "贵州都匀"],
        "products": [
            "西湖龙井茶 明前特级 250g 正宗杭州绿茶",
            "安溪铁观音 清香型 500g 福建乌龙茶",
            "云南普洱茶 熟茶饼 357g 古树陈年普洱",
            "武夷山大红袍 岩茶 250g 正宗武夷岩茶",
            "信阳毛尖 明前特级 250g 河南绿茶",
            "碧螺春 特级绿茶 250g 江苏苏州洞庭山",
            "金骏眉红茶 特级 250g 福建武夷山红茶",
            "福鼎白茶 白牡丹 350g 陈年白茶饼",
            "黄山毛峰 特级 250g 安徽绿茶 明前新茶",
            "安化黑茶 茯砖茶 500g 湖南益阳黑茶",
            "茉莉花茶 250g 福州茉莉花窨制 浓香型",
            "正山小种 红茶 250g 武夷山桐木关",
            "都匀毛尖 特级绿茶 250g 贵州名茶",
            "凤凰单丛 鸭屎香 250g 广东潮州乌龙茶",
        ],
    },
    "生鲜": {
        "en": "Fresh Produce",
        "count": 500,
        "price_mean": 55, "price_std": 40, "price_min": 10, "price_max": 300,
        "sales_base": 450, "sales_std": 350,
        "review_rate": 0.07,
        "rating_mean": 4.3, "rating_std": 0.5,
        "origins": ["内蒙古锡林郭勒", "山东潍坊", "辽宁大连", "浙江舟山", "广东湛江",
                    "江苏苏州", "四川成都", "湖北武汉", "福建厦门", "河北沧州"],
        "products": [
            "澳洲进口牛排 原切西冷 10片装 1500g",
            "内蒙古羊肉卷 3斤装 草原散养 新鲜羊肉",
            "新鲜三文鱼 整块中段 500g 空运冰鲜",
            "舟山带鱼 中段 2斤装 新鲜冷冻 海鲜水产",
            "农家散养土鸡蛋 30枚装 新鲜初生蛋",
            "青岛大虾 鲜活冷冻 2斤装 30-40只/斤",
            "新鲜猪肋排 3斤装 冷鲜黑猪肉 整扇排骨",
            "内蒙古牛腩块 2斤装 草饲牛肉 炖煮佳品",
            "新鲜鸡胸肉 3斤装 去皮去骨 低脂高蛋白",
            "阳澄湖大闸蟹 8只装 鲜活螃蟹 顺丰空运",
            "新鲜鸡翅中 2斤装 冷冻鸡中翅 烧烤食材",
            "乳山生蚝 5斤装 鲜活牡蛎 顺丰冷链",
            "原切肥牛卷 3斤装 火锅食材 谷饲肥牛",
            "新鲜鲈鱼 鲜活清蒸 2条装 约500g/条",
            "丹麦进口五花肉 3斤装 谷饲猪肉 肥瘦相间",
        ],
    },
}

OUTPUT_PATH = "data/raw/raw_data.csv"


def generate_price(cfg):
    """Generate a realistic price from a lognormal-like distribution."""
    while True:
        price = np.random.lognormal(
            mean=np.log(cfg["price_mean"]),
            sigma=cfg["price_std"] / cfg["price_mean"],
        )
        if cfg["price_min"] <= price <= cfg["price_max"]:
            return round(price, 2)


def generate_sales(cfg):
    """Generate sales volume — right-skewed, most products sell moderate amounts."""
    return max(10, int(np.random.lognormal(
        mean=np.log(cfg["sales_base"]),
        sigma=cfg["sales_std"] / cfg["sales_base"],
    )))


def generate_rating(cfg):
    """Generate rating 1-5, centered around category mean, clamped."""
    rating = np.random.normal(cfg["rating_mean"], cfg["rating_std"])
    return round(max(1.0, min(5.0, rating)), 1)


def main():
    all_records = []
    product_id = 0

    for cat_label, cfg in CATEGORY_CONFIG.items():
        count = cfg["count"]
        products = cfg["products"]
        origins = cfg["origins"]

        for i in range(count):
            product_id += 1
            product_template = random.choice(products)
            product_name = f"[{chr(65 + random.randint(0, 25))}{chr(65 + random.randint(0, 25))}品牌] {product_template}"

            price = generate_price(cfg)
            sales_volume = generate_sales(cfg)
            review_count = max(0, int(sales_volume * cfg["review_rate"] * random.uniform(0.3, 2.5)))
            rating = generate_rating(cfg)
            origin = random.choice(origins)
            is_promoted = 1 if random.random() < 0.35 else 0

            # Shipping location (usually same province as origin)
            shipping_map = {
                "山东": "山东济南", "海南": "海南海口", "广西": "广西南宁",
                "新疆": "新疆乌鲁木齐", "陕西": "陕西西安", "广东": "广东广州",
                "云南": "云南昆明", "四川": "四川成都", "福建": "福建福州",
                "江西": "江西南昌", "浙江": "浙江杭州", "河北": "河北石家庄",
                "河南": "河南郑州", "江苏": "江苏南京", "辽宁": "辽宁沈阳",
                "安徽": "安徽合肥", "湖北": "湖北武汉", "湖南": "湖南长沙",
                "吉林": "吉林长春", "黑龙江":"黑龙江哈尔滨", "贵州": "贵州贵阳",
                "内蒙古": "内蒙古呼和浩特",
            }
            province = origin[:2]
            shipping = shipping_map.get(province, origin)

            # Store name
            store_names = ["苏宁自营", "苏宁自营", "苏宁自营",  # 75% self-operated
                          f"{province}农产品旗舰店",
                          f"{province}果蔬专营店"]
            store_name = random.choice(store_names)

            # Store level (for flagship stores, etc.)
            store_level = None
            if "旗舰" in store_name:
                store_level = "旗舰店"
            elif "专营" in store_name:
                store_level = "专营店"

            # Price tier
            if price < 20:
                price_tier = "budget"
            elif price < 80:
                price_tier = "mid"
            else:
                price_tier = "premium"

            all_records.append({
                "product_name":       product_name,
                "category":           cat_label,
                "category_en":        cfg["en"],
                "price":              price,
                "sales_volume":       sales_volume,
                "review_count":       review_count,
                "rating":             rating,
                "origin":             origin,
                "shipping_location":  shipping,
                "store_name":         store_name,
                "store_level":        store_level,
                "is_promoted":        is_promoted,
                "product_url":        None,
                "sku_id":             f"GEN{product_id:06d}",
                "price_tier":         price_tier,
            })

    # Save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df = pd.DataFrame(all_records)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Generated {len(df)} records across {df['category'].nunique()} categories")
    print(f"\nCategory breakdown:")
    for cat in CATEGORY_CONFIG:
        subset = df[df["category"] == cat]
        print(f"  {cat:4s} ({CATEGORY_CONFIG[cat]['en']:20s}): "
              f"{len(subset):4d} records  "
              f"avg price=¥{subset['price'].mean():.1f}  "
              f"avg sales={subset['sales_volume'].mean():.0f}  "
              f"avg rating={subset['rating'].mean():.2f}")
    print(f"\nOutput: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
