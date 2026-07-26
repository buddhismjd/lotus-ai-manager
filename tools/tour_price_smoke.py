from decimal import Decimal

from backend.structured_catalog.models import StructuredTour
from backend.tours.collection_builder import _published_item
from backend.tours.price_parser import parse_tour_price


def main() -> None:
    parsed = parse_tour_price("Стоимость тура: 3 250 USD")
    assert parsed is not None
    assert parsed.amount == Decimal("3250")
    card = _published_item(StructuredTour(
        id="tour", title="Тестовый тур", url="https://example.test/tour",
        price=parsed.amount, currency=parsed.currency,
    ))
    assert card.price == "3 250 $"
    print("tour_price_parser=OK")
    print("tour_card_price=OK")


if __name__ == "__main__":
    main()
