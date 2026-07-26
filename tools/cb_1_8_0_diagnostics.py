from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from decimal import Decimal

from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product
from backend.catalog.recommendation_engine import analyze_recommendation_query


def product(index: int, description: str) -> Product:
    return Product(
        id=f"diag-{index}",
        title=f"Подарок {index}",
        description=description,
        category="Буддийские товары",
        price=Decimal("1500"),
        currency="RUB",
        availability_status="В наличии",
        url=f"https://example.test/{index}",
    )


intent = analyze_recommendation_query("Подберите подарок")
assert intent.usage == "gift" and intent.result_limit == 6
print("commercial_intent=OK")

items = build_product_collection(
    "Подберите подарок",
    [product(i, "Подходит в подарок") for i in range(8)],
)
assert len(items) == 6
print("deterministic_recommendation_limit=OK")

all_items = build_product_collection(
    "Покажи все товары с Калачакрой",
    [
        Product(
            id=f"all-{i}",
            title=f"Калачакра {i}",
            description="Калачакра",
            category="Буддийские товары",
            price=Decimal("2000"),
            currency="RUB",
            availability_status="В наличии",
            url=f"https://example.test/all-{i}",
        )
        for i in range(8)
    ],
)
assert len(all_items) == 8
print("exhaustive_query_preserved=OK")
