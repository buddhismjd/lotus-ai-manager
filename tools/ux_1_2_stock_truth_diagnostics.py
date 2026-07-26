from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product


def main() -> None:
    product = Product(
        id="diagnostic-green-tara",
        title="Статуя Зелёной Тары",
        url="https://example.test/tproduct/green-tara",
        availability_status=None,
        available=True,
    )
    item = build_product_collection("статуя Зелёной Тары", [product])[0]
    assert item.availability is None
    assert item.group == "Наличие уточняется"
    print("UX-1.2 diagnostic: PASS")
    print("Unknown stock is not presented as 'В наличии'.")


if __name__ == "__main__":
    main()
