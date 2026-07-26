from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product
from backend.catalog.product_intelligence import analyze_product


def product(product_id: str, title: str, category: str) -> Product:
    return Product(id=product_id, title=title, category=category, url=f"https://example.test/{product_id}")


assert "Калачакра" in analyze_product(title="Наклейка Калачакра").entities
print("aspect_detection=OK")

products = [
    product("1", "Статуя Калачакры", "Статуи"),
    product("2", "Тханка Калачакры", "Тханки"),
    product("3", "Защитная наклейка Калачакра", "Наклейки"),
]
items = build_product_collection("что-нибудь с Калачакрой", products)
assert len(items) == 3
assert len({item.category for item in items}) == 3
print("cross_category_aspect_collection=OK")
