from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from decimal import Decimal

from backend.catalog.collection_builder import build_product_collection
from backend.catalog.commercial_cards import commercial_cards
from backend.catalog.models import Product

products = [
    Product(
        id="altar-1",
        title="Статуя для алтаря",
        description="Для домашнего алтаря",
        category="Статуи",
        price=Decimal("9900"),
        currency="RUB",
        availability_status="В наличии",
        url="https://example.test/altar-1",
    ),
]

cards = commercial_cards(build_product_collection("Что подобрать для домашнего алтаря?", products))
assert len(cards) == 1
assert set(cards[0]) == {
    "id", "item_type", "title", "image_url", "price", "availability",
    "url", "button_label", "status",
}
assert cards[0]["button_label"] == "Открыть товар"
print("commercial_recommendation_card=OK")
