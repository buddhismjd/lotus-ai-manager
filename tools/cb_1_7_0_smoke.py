from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from decimal import Decimal

from backend.catalog.models import Product
from backend.sales_assistant.product_selection import ProductSelectionService
from backend.sales_assistant.selection_page import _render_product_card

product = Product(
    id="white-tara",
    title="Статуя Белой Тары",
    url="https://example.test/white-tara",
    description="Большое описание, которого не должно быть в карточке.",
    material="Латунь",
    height_cm=18,
    price=Decimal("25000"),
    currency="RUB",
    availability_status="В наличии",
    image_url="https://example.test/white-tara.jpg",
)
html = _render_product_card(product, ProductSelectionService())
assert "25 000 ₽" in html
assert "В наличии" in html
assert "Открыть товар" in html
assert "Большое описание" not in html
assert "Латунь" not in html
assert "18 см" not in html
print("minimal_product_card=OK")
