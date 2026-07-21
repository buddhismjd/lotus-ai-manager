from __future__ import annotations

from backend.sales_assistant.strategy import choose_strategy
from backend.sales_assistant.tour_discovery import (
    filter_tours_for_query,
    understand_tour_query,
)
from backend.structured_catalog.models import StructuredTour, TourSchedule


def _tour(
    tour_id: str,
    title: str,
    *,
    schedule: TourSchedule,
    aspects: tuple[str, ...] = (),
    teachers: tuple[str, ...] = (),
    country: str = "",
    description: str = "",
) -> StructuredTour:
    return StructuredTour(
        id=tour_id,
        title=title,
        url=f"https://example.test/{tour_id}",
        description=description,
        schedule=schedule,
        countries=(country,) if country else (),
        aspects=aspects,
        teachers=teachers,
    )


def test_guru_rinpoche_places_are_understood_as_tour_constraint() -> None:
    query = understand_tour_query("А по местам Гуру Ринпоче возите?")
    assert query.aspects == ("Гуру Ринпоче",)
    assert query.constrained is True
    assert choose_strategy("А по местам Гуру Ринпоче возите?", "tour").strategy == "tour_list"


def test_guru_rinpoche_query_returns_tours_not_unrelated_catalog_items() -> None:
    tours = [
        _tour(
            "bhutan",
            "Бутан с Гуру Ринпоче и Ваджрайогини",
            schedule=TourSchedule(1, 11, 7, 11),
            aspects=("Гуру Ринпоче",),
            teachers=("Гуру Ринпоче",),
            country="Бутан",
        ),
        _tour(
            "kailas",
            "Тибет + Кайлас",
            schedule=TourSchedule(22, 9, 9, 10),
            country="Тибет",
        ),
    ]
    assert filter_tours_for_query(
        tours,
        "А по местам Гуру Ринпоче возите?",
    ) == [tours[0]]


def test_new_year_holidays_are_resolved_to_date_window() -> None:
    tours = [
        _tour(
            "new-year",
            "Новогодний тур",
            schedule=TourSchedule(28, 12, 8, 1),
        ),
        _tour(
            "may",
            "Весенний тур",
            schedule=TourSchedule(2, 5, 11, 5),
        ),
    ]
    assert filter_tours_for_query(
        tours,
        "Какие туры есть в новогодние праздники?",
    ) == [tours[0]]


def test_natural_period_with_no_matches_returns_empty_list_not_all_tours() -> None:
    tours = [
        _tour(
            "summer",
            "Летний тур",
            schedule=TourSchedule(1, 7, 10, 7),
        ),
    ]
    assert filter_tours_for_query(
        tours,
        "Какие туры есть в новогодние праздники?",
    ) == []


def test_time_is_never_imposed_when_user_did_not_name_it() -> None:
    query = understand_tour_query("Какие туры есть?")
    assert query.natural_periods == ()


def test_early_december_does_not_count_as_new_year_holidays() -> None:
    tour = _tour(
        "early-december",
        "Начало декабря",
        schedule=TourSchedule(1, 12, 10, 12),
    )
    assert filter_tours_for_query(
        [tour],
        "Какие туры есть в новогодние праздники?",
    ) == []
