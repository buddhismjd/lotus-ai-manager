from __future__ import annotations

from backend.sales_assistant.tour_discovery import filter_tours_for_query
from backend.structured_catalog.models import StructuredTour, TourSchedule


def main() -> None:
    tours = [
        StructuredTour(
            id="nepal",
            title="Лапчи — место силы Миларепы",
            url="https://example.test/nepal",
            countries=("Непал",),
            schedule=TourSchedule(4, 11, 11, 11, source_text="4–11 ноября"),
        ),
        StructuredTour(
            id="tibet",
            title="Тибет + Кайлас",
            url="https://example.test/tibet",
            countries=("Тибет",),
            schedule=TourSchedule(22, 9, 9, 10, source_text="22 сентября – 9 октября"),
        ),
    ]
    result = filter_tours_for_query(tours, "Хочу в Непал")
    assert [tour.id for tour in result] == ["nepal"]
    print("SMOKE PASSED")
    print("Natural request: Хочу в Непал")
    print(f"Tours returned: {len(result)}")


if __name__ == "__main__":
    main()
