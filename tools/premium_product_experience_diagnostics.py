from backend.catalog.models import Product
from backend.sales_assistant.product_selection import ProductSelectionService
from backend.sales_assistant.selection_page import _render_product_card
from backend.sales_assistant.tone import TONE


def main() -> None:
    product = Product(
        id="diagnostic-statue",
        title="Статуя Зеленой Тары",
        url="https://example.com/statue",
        description="Высота: 14 см",
        material="бронза",
        availability_status="Под заказ",
        image_url="https://example.com/statue.jpg",
    )
    card = _render_product_card(product, ProductSelectionService())
    checks = {
        "short_greeting": TONE.greeting.startswith("Добрый день! Буду рада помочь!"),
        "image": "statue.jpg" in card,
        "height": "Высота: 14 см" in card,
        "material": "Материал: бронза" in card,
        "status": "Под заказ" in card,
        "button": "Открыть товар" in card,
    }
    print("AI BODHI PREMIUM PRODUCT EXPERIENCE DIAGNOSTICS")
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
