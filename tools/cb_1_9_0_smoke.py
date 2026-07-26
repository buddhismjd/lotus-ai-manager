from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.catalog.collection_builder import CollectionItem
from backend.sales_assistant import service as service_module
from backend.sales_assistant.service import SalesAssistant


def main() -> None:
    original = service_module.build_product_collection
    try:
        service_module.build_product_collection = lambda query, *args, **kwargs: [CollectionItem(
            id="smoke-product",
            title="Товар для выбора",
            url="https://example.test/product",
            image_url="https://example.test/product.jpg",
            price="5 000 ₽",
            availability="В наличии",
        )]
        assistant = SalesAssistant()
        first = assistant.reply("Хочу подарок", session_id="cb-1-9-smoke")
        second = assistant.reply("Для буддийской практики", session_id="cb-1-9-smoke")
        assert first.kind == "commercial_clarification"
        assert second.kind == "product_collection"
        assert second.items[0]["button_label"] == "Открыть товар"
        print("one_question_then_commercial_cards=OK")
    finally:
        service_module.build_product_collection = original


if __name__ == "__main__":
    main()
