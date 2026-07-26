from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.catalog.collection_builder import CollectionItem
from backend.catalog.commercial_cards import commercial_card

product = commercial_card(CollectionItem(
    id="product",
    title="Статуя Белой Тары",
    url="https://example.test/product",
    image_url="https://example.test/product.jpg",
    price="25 000 ₽",
    availability="В наличии",
    description="Не должно попасть в карточку",
    material="Латунь",
    size="18 см",
    item_type="product",
))
tour = commercial_card(CollectionItem(
    id="tour",
    title="Непал — Лапчи",
    url="https://example.test/tour",
    image_url="https://example.test/tour.jpg",
    price="1 450 $",
    availability="4–11 ноября 2026",
    description="Не должно попасть в карточку",
    item_type="tour",
))

assert set(product) == {"id", "item_type", "title", "image_url", "price", "availability", "url", "button_label", "status"}
assert product["button_label"] == "Открыть товар"
assert tour["button_label"] == "Открыть тур"
assert tour["price"] and tour["availability"]
print("commercial_card_contract=OK")
print("product_required_fields=OK")
print("tour_required_fields=OK")
