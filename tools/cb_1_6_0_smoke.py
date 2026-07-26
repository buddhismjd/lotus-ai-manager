from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product

products = [
    Product(id="statue", title="Статуя Калачакры", category="Статуи", url="https://example.test/statue", image_url="https://img.test/statue.jpg"),
    Product(id="thangka", title="Тханка Калачакры", category="Тханки", url="https://example.test/thangka", image_url="https://img.test/thangka.jpg"),
    Product(id="sticker", title="Наклейка Калачакра", category="Наклейки", url="https://example.test/sticker", image_url="https://img.test/sticker.jpg"),
]

broad = build_product_collection("Покажи всё с Калачакрой", products)
assert {item.id for item in broad} == {"statue", "thangka", "sticker"}
assert all(item.image_url for item in broad)
print("broad_aspect_search=OK")

filtered = build_product_collection("Покажи тханку Калачакры", products)
assert [item.id for item in filtered] == ["thangka"]
print("aspect_plus_category_search=OK")
