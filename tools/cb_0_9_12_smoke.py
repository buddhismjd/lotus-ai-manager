from __future__ import annotations

from decimal import Decimal

from backend.catalog.collection_builder import build_product_items
from backend.catalog.models import Product


def main() -> int:
    products = [
        Product(
            id="tara-1",
            title="Статуя Белой Тары",
            url="https://example.test/tara-1",
            image_url="https://example.test/tara-1.jpg",
            price=Decimal("100"),
            material="Латунь",
            height_cm=18,
            availability_status="В наличии",
        ),
        Product(
            id="tara-2",
            title="Статуя Белой Тары",
            url="https://example.test/tara-2",
            image_url="https://example.test/tara-2.jpg",
            material="Бронза",
            height_cm=22,
            availability_status="Под заказ",
        ),
    ]
    items = build_product_items(products)
    passed = len(items) == 2 and all(item.image_url and item.url for item in items)
    print(f"cards={len(items)}")
    print(f"complete_cards={'OK' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
