from __future__ import annotations

from backend.catalog.models import Tour
from backend.structured_catalog.builders import build_structured_tour
from backend.structured_catalog.date_parser import parse_tour_schedule
from backend.structured_catalog.repositories import StructuredTourRepository


class _Source:
    def __init__(self, tours: list[Tour]) -> None:
        self.tours = tours

    def list_all(self, enabled_only: bool = True) -> list[Tour]:
        return list(self.tours)

    def get_by_id(self, tour_id: str) -> Tour | None:
        return next((tour for tour in self.tours if tour.id == tour_id), None)


def _tour(identifier: str, title: str, description: str) -> Tour:
    return Tour(
        id=identifier,
        title=title,
        url=f"https://example.test/{identifier}",
        description=description,
        metadata={"page_type": "tour"},
    )


def test_parser_handles_range_with_two_months() -> None:
    schedule = parse_tour_schedule("22 сентября – 9 октября")
    assert schedule is not None
    assert (schedule.start_month, schedule.end_month) == (9, 10)
    assert schedule.includes_month(9)
    assert schedule.includes_month(10)
    assert not schedule.includes_month(11)


def test_parser_handles_range_with_one_month() -> None:
    schedule = parse_tour_schedule("3 — 14 сентября")
    assert schedule is not None
    assert (schedule.start_day, schedule.end_day) == (3, 14)
    assert schedule.start_month == schedule.end_month == 9


def test_builder_does_not_invent_calendar_year() -> None:
    structured = build_structured_tour(
        _tour("kailash", "Тибет + Кайлас — 18 дней", "22 сентября – 9 октября")
    )
    assert structured.schedule is not None
    assert structured.schedule.year is None
    assert structured.duration_days == 18


def test_repository_filters_all_tours_intersecting_month() -> None:
    source = _Source(
        [
            _tour("markha", "Долина Маркха", "3 — 14 сентября"),
            _tour("kailash", "Тибет + Кайлас", "22 сентября – 9 октября"),
            _tour("bhutan", "Бутан", "1 – 7 ноября"),
        ]
    )
    repository = StructuredTourRepository(source=source)  # type: ignore[arg-type]
    assert [tour.id for tour in repository.list_by_month(9)] == ["markha", "kailash"]
    assert [tour.id for tour in repository.list_by_month(10)] == ["kailash"]
    assert [tour.id for tour in repository.list_by_month(11)] == ["bhutan"]


def test_repository_rejects_invalid_month() -> None:
    repository = StructuredTourRepository(source=_Source([]))  # type: ignore[arg-type]
    try:
        repository.list_by_month(13)
    except ValueError as exc:
        assert "between 1 and 12" in str(exc)
    else:
        raise AssertionError("ValueError was not raised")
