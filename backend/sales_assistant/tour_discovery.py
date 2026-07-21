from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from backend.structured_catalog.models import StructuredTour, TourSchedule


DIRECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "Тибет": ("тибет", "тибетск"),
    "Индия": ("индия", "индии", "индийск", "ладакх", "занскар"),
    "Бутан": ("бутан", "бутане", "бутанск"),
    "Непал": ("непал", "непале", "непальск", "лапчи"),
    "Япония": ("япония", "японии", "японск"),
}

DESTINATION_ALIASES: dict[str, tuple[str, ...]] = {
    "Кайлас": ("кайлас", "кайлаш"),
    "Лапчи": ("лапчи",),
    "Миларепа": ("милареп",),
    "Гуру Ринпоче": ("гуру ринпоче", "падмасамбхав"),
}

ASPECT_ALIASES: dict[str, tuple[str, ...]] = {
    "Гуру Ринпоче": ("гуру ринпоче", "падмасамбхав"),
    "Миларепа": ("милареп",),
}

# Natural periods are interpreted only when the user names them. AI Bodhi
# never asks the user to select a month or season.
NATURAL_TIME_ALIASES: dict[str, tuple[str, ...]] = {
    "new_year_holidays": (
        "новогодние праздники",
        "новогодних праздниках",
        "на новый год",
        "новый год",
        "рождественские праздники",
    ),
    "may_holidays": (
        "майские праздники",
        "на майские",
        "майские выходные",
    ),
}


@dataclass(frozen=True, slots=True)
class TourDiscoveryQuery:
    directions: tuple[str, ...] = ()
    destinations: tuple[str, ...] = ()
    aspects: tuple[str, ...] = ()
    natural_periods: tuple[str, ...] = ()

    @property
    def constrained(self) -> bool:
        return bool(
            self.directions
            or self.destinations
            or self.aspects
            or self.natural_periods
        )


def _normalise(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


def _matched_labels(
    query: str,
    aliases: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    text = _normalise(query)
    return tuple(
        label
        for label, variants in aliases.items()
        if any(_normalise(variant) in text for variant in variants)
    )


def understand_tour_query(query: str) -> TourDiscoveryQuery:
    """Extract only conditions explicitly present in the user's request."""
    return TourDiscoveryQuery(
        directions=_matched_labels(query, DIRECTION_ALIASES),
        destinations=_matched_labels(query, DESTINATION_ALIASES),
        aspects=_matched_labels(query, ASPECT_ALIASES),
        natural_periods=_matched_labels(query, NATURAL_TIME_ALIASES),
    )


def _tour_text(tour: StructuredTour) -> str:
    values = (
        tour.title,
        tour.description,
        *tour.countries,
        *tour.regions,
        *tour.destinations,
        *tour.aspects,
        *tour.teachers,
        *tour.keywords,
    )
    return _normalise(" ".join(value for value in values if value))


def _matches_label(
    text: str,
    label: str,
    aliases: dict[str, tuple[str, ...]],
) -> bool:
    variants = aliases.get(label, (label,))
    return any(_normalise(variant) in text for variant in variants)


def _day_of_year(month: int, day: int) -> int:
    return date(2000, month, day).timetuple().tm_yday


def _circular_segments(start: int, end: int) -> tuple[tuple[int, int], ...]:
    year_end = _day_of_year(12, 31)
    if start <= end:
        return ((start, end),)
    return ((start, year_end), (1, end))


def _ranges_overlap(
    left: tuple[tuple[int, int], ...],
    right: tuple[tuple[int, int], ...],
) -> bool:
    return any(
        max(left_start, right_start) <= min(left_end, right_end)
        for left_start, left_end in left
        for right_start, right_end in right
    )


def _schedule_intersects_period(schedule: TourSchedule, period: str) -> bool:
    periods = {
        "new_year_holidays": ((12, 25), (1, 10)),
        "may_holidays": ((4, 28), (5, 12)),
    }
    boundaries = periods.get(period)
    if boundaries is None:
        return False

    (period_start_month, period_start_day), (
        period_end_month,
        period_end_day,
    ) = boundaries
    schedule_segments = _circular_segments(
        _day_of_year(schedule.start_month, schedule.start_day),
        _day_of_year(schedule.end_month, schedule.end_day),
    )
    period_segments = _circular_segments(
        _day_of_year(period_start_month, period_start_day),
        _day_of_year(period_end_month, period_end_day),
    )
    return _ranges_overlap(schedule_segments, period_segments)


def matches_tour(tour: StructuredTour, discovery: TourDiscoveryQuery) -> bool:
    if tour.schedule is None:
        return False

    text = _tour_text(tour)
    if discovery.directions and not any(
        _matches_label(text, label, DIRECTION_ALIASES)
        for label in discovery.directions
    ):
        return False
    if discovery.destinations and not any(
        _matches_label(text, label, DESTINATION_ALIASES)
        for label in discovery.destinations
    ):
        return False
    if discovery.aspects and not any(
        _matches_label(text, label, ASPECT_ALIASES)
        for label in discovery.aspects
    ):
        return False
    if discovery.natural_periods and not any(
        _schedule_intersects_period(tour.schedule, period)
        for period in discovery.natural_periods
    ):
        return False
    return True


def filter_tours_for_query(
    tours: list[StructuredTour],
    query: str,
) -> list[StructuredTour]:
    discovery = understand_tour_query(query)
    return [tour for tour in tours if matches_tour(tour, discovery)]


def available_directions(tours: list[StructuredTour]) -> tuple[str, ...]:
    """Return website-facing directions represented by the current results."""
    result: list[str] = []
    for label in DIRECTION_ALIASES:
        if any(
            _matches_label(_tour_text(tour), label, DIRECTION_ALIASES)
            for tour in tours
        ):
            result.append(label)
    return tuple(result)


__all__ = [
    "ASPECT_ALIASES",
    "DIRECTION_ALIASES",
    "DESTINATION_ALIASES",
    "NATURAL_TIME_ALIASES",
    "TourDiscoveryQuery",
    "available_directions",
    "filter_tours_for_query",
    "matches_tour",
    "understand_tour_query",
]
