from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product
from backend.structured_catalog.models import StructuredTour
from backend.tours.collection_builder import build_tour_collection


def main() -> int:
    product = Product(
        id="bell",
        title="Ритуальный колокольчик Ганта",
        url="https://svet-lotosa.tilda.ws/tproduct/2-bell",
    )
    product_items = build_product_collection("Колокольчик имеется?", [product])
    print(f"product_cards={len(product_items)}")
    print(f"product_image={product_items[0].image_url if product_items else None}")
    return 0 if product_items and product_items[0].image_url else 1


if __name__ == "__main__":
    raise SystemExit(main())
