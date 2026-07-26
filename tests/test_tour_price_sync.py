from decimal import Decimal

from backend.catalog import repositories
from backend.tours.collection_builder import _published_item
from backend.tours.price_parser import parse_tour_price
from backend.structured_catalog.models import StructuredTour


def test_parser_extracts_labeled_ruble_price() -> None:
    price = parse_tour_price("Стоимость тура: 185 000 руб. В стоимость входит трансфер")
    assert price is not None
    assert price.amount == Decimal("185000")
    assert price.currency == "RUR"


def test_parser_extracts_usd_and_euro_prices() -> None:
    usd = parse_tour_price("Стоимость путешествия — 3 250 USD")
    eur = parse_tour_price("Цена программы: € 2400")
    assert usd is not None and (usd.amount, usd.currency) == (Decimal("3250"), "USD")
    assert eur is not None and (eur.amount, eur.currency) == (Decimal("2400"), "EUR")


def test_parser_does_not_invent_price_from_inclusion_heading_or_dates() -> None:
    text = "4–11 ноября 2026 года\nВ стоимость входит\nТрансфер и проживание"
    assert parse_tour_price(text) is None


def test_tour_repository_maps_price_from_document_content() -> None:
    row = {
        "id": "lapchi",
        "title": "Лапчи",
        "url": "https://example.test/lapchi",
        "summary": "Паломнический тур",
        "content": "Стоимость поездки: 2 900 USD",
        "source_type": "tilda",
        "page_type": "tour",
        "priority": 10,
        "content_hash": "x",
        "created_at": None,
        "updated_at": None,
    }
    tour = repositories._row_to_tour(_Row(row))
    assert tour.price == Decimal("2900")
    assert tour.currency == "USD"
    assert tour.metadata["price_source_text"] == "Стоимость поездки: 2 900 USD"


def test_tour_card_contains_formatted_price() -> None:
    tour = StructuredTour(
        id="kailas",
        title="Тибет + Кайлас",
        url="https://example.test/kailas",
        price=Decimal("3250"),
        currency="USD",
    )
    item = _published_item(tour)
    assert item.price == "3 250 $"


class _Row:
    def __init__(self, values: dict):
        self._values = values

    def __getitem__(self, key):
        return self._values[key]

    def keys(self):
        return self._values.keys()


def test_parser_extracts_tilda_header_from_price_with_comma_separator() -> None:
    price = parse_tour_price("Нестандартный тур в Бутан\nот $ 1,450\n1–7 ноября")
    assert price is not None
    assert price.amount == Decimal("1450")
    assert price.currency == "USD"
    assert price.source_text == "от $ 1,450"
    assert price.is_from is True


def test_parser_ignores_unlabeled_route_supplements() -> None:
    text = "Въезд в Мустанг $30\nОдноместное размещение +410 $"
    assert parse_tour_price(text) is None


def test_tour_card_preserves_from_price_prefix() -> None:
    tour = StructuredTour(
        id="bhutan",
        title="Бутан",
        url="https://example.test/bhutan",
        price=Decimal("1450"),
        currency="USD",
        metadata={"price_is_from": True},
    )
    item = _published_item(tour)
    assert item.price == "от 1 450 $"
