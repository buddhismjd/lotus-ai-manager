from backend.catalog.models import Product
from backend.sales_assistant.product_selection import ProductSelectionService
from backend.sales_assistant.selection_page import _render_product_card


def main() -> None:
    card = _render_product_card(
        Product(
            id="smoke",
            title="Статуя Будды",
            url="https://example.com/buddha",
            description="Высота: 12 см",
            material="латунь",
            availability_status="В наличии",
            image_url="https://example.com/buddha.jpg",
        ),
        ProductSelectionService(),
    )
    required = ("buddha.jpg", "Высота: 12 см", "Материал: латунь", "В наличии", "Открыть товар")
    if not all(value in card for value in required):
        raise SystemExit("SMOKE FAILED")
    print("SMOKE PASSED")


if __name__ == "__main__":
    main()
