from __future__ import annotations

from backend.sales_assistant.formatter import format_tour_list
from backend.sales_assistant.strategy import choose_strategy
from backend.sales_assistant.tour_discovery import (
    available_directions,
    filter_tours_for_query,
    understand_tour_query,
)
from backend.structured_catalog.models import StructuredTour, TourSchedule


def _tour(
    tour_id: str,
    title: str,
    *,
    country: str = "",
    description: str = "",
    scheduled: bool = True,
) -> StructuredTour:
    return StructuredTour(
        id=tour_id,
        title=title,
        url=f"https://example.test/{tour_id}",
        description=description,
        schedule=(
            TourSchedule(1, 9, 10, 9, source_text="1–10 сентября")
            if scheduled
            else None
        ),
        duration_days=10,
        countries=(country,) if country else (),
    )


def test_generic_list_returns_every_scheduled_tour_without_limit() -> None:
    tours = [_tour(str(index), f"Тур {index}") for index in range(1, 9)]
    answer = format_tour_list(tours)
    assert all(f"Тур {index}" in answer for index in range(1, 9))


def test_unscheduled_programs_are_not_part_of_discovery() -> None:
    scheduled = _tour("scheduled", "Опубликованный тур")
    planned = _tour("planned", "Программа готовится", scheduled=False)
    assert filter_tours_for_query([scheduled, planned], "Какие туры есть?") == [scheduled]


def test_nepal_query_returns_only_nepal_tours() -> None:
    tours = [
        _tour("nepal", "Лапчи", country="Непал"),
        _tour("tibet", "Тибет + Кайлас", country="Тибет"),
    ]
    assert filter_tours_for_query(tours, "Хочу поехать в Непал") == [tours[0]]


def test_kailas_query_matches_destination_without_questionnaire() -> None:
    tours = [
        _tour("kailas", "Тибет + Кайлас", country="Тибет"),
        _tour("markha", "Долина Маркха", country="Индия"),
    ]
    assert filter_tours_for_query(tours, "Хочу на Кайлас") == [tours[0]]
    assert choose_strategy("Хочу на Кайлас", "tour").strategy == "tour_list"


def test_direction_buttons_are_derived_from_current_catalog() -> None:
    tours = [
        _tour("nepal", "Лапчи", country="Непал"),
        _tour("india", "Ладакх", country="Индия"),
    ]
    assert available_directions(tours) == ("Индия", "Непал")


def test_query_understanding_does_not_impose_trekking_or_difficulty() -> None:
    query = understand_tour_query("Покажите все туры")
    assert query.directions == ()
    assert query.destinations == ()
