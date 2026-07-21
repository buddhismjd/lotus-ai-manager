from __future__ import annotations

from backend.sales_assistant.tour_discovery import filter_tours_for_query
from backend.structured_catalog.models import StructuredTour, TourSchedule


def main() -> None:
    guru_tour = StructuredTour(
        id="guru-rinpoche",
        title="Бутан с Гуру Ринпоче",
        url="https://example.test/guru-rinpoche",
        schedule=TourSchedule(1, 11, 7, 11),
        aspects=("Гуру Ринпоче",),
    )
    unrelated = StructuredTour(
        id="unrelated",
        title="Тибет + Кайлас",
        url="https://example.test/kailas",
        schedule=TourSchedule(22, 9, 9, 10),
    )
    result = filter_tours_for_query(
        [guru_tour, unrelated],
        "По местам Гуру Ринпоче возите?",
    )
    assert result == [guru_tour]
    print("SMOKE PASSED")
    print(f"Matched tour: {result[0].title}")


if __name__ == "__main__":
    main()
