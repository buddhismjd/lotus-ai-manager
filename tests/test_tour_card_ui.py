from backend.structured_catalog.models import StructuredTour
from backend.tours.collection_builder import _published_item


def test_tour_card_has_only_page_button_and_no_duration_field() -> None:
    tour = StructuredTour(
        id="lapchi",
        title="Непал — Лапчи, место силы Миларепы",
        url="https://example.test/lapchi",
        duration_days=14,
        description="Паломническое путешествие в Лапчи.",
    )

    item = _published_item(tour)

    assert item.button_label == "Открыть тур"
    assert item.size is None
