from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Literal

from backend.catalog.models import Tour

SalesStrategy = Literal[
    "tour_list",
    "tour_details",
    "tour_price",
    "tour_date",
    "product_search",
    "service_info",
    "contacts",
    "fallback",
]

MONTHS = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "ма": 5,
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
}

LIST_MARKERS = (
    "какие тур",
    "какие поезд",
    "какие путешеств",
    "что есть из тур",
    "покажите тур",
    "покажи тур",
    "список тур",
)
DETAIL_MARKERS = ("расскаж", "подроб", "программ", "что входит", "условия")
PRICE_MARKERS = ("цен", "стоим", "сколько стоит")
DATE_MARKERS = ("когда", "дат", "в каком месяц")


@dataclass(frozen=True, slots=True)
class StrategyDecision:
    strategy: SalesStrategy
    month: int | None = None
    country: str | None = None


def _normalise(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


def detect_month(query: str) -> int | None:
    normalised = _normalise(query)
    for prefix, month in MONTHS.items():
        if prefix in normalised:
            return month
    return None


def choose_strategy(query: str, topic: str) -> StrategyDecision:
    normalised = _normalise(query)

    if topic == "tour":
        month = detect_month(normalised)
        if month is not None or any(marker in normalised for marker in LIST_MARKERS):
            return StrategyDecision("tour_list", month=month)
        if any(marker in normalised for marker in PRICE_MARKERS):
            return StrategyDecision("tour_price")
        if any(marker in normalised for marker in DATE_MARKERS):
            return StrategyDecision("tour_date")
        if any(marker in normalised for marker in DETAIL_MARKERS):
            return StrategyDecision("tour_details")
        return StrategyDecision("tour_details")

    if topic == "product":
        return StrategyDecision("product_search")
    if topic == "psychologist":
        return StrategyDecision("service_info")
    if topic == "contacts":
        return StrategyDecision("contacts")
    return StrategyDecision("fallback")


def _month_from_text(value: str) -> int | None:
    return detect_month(value)


def tour_months(tour: Tour) -> set[int]:
    months: set[int] = set()
    if tour.start_date:
        months.add(tour.start_date.month)
    if tour.end_date:
        months.add(tour.end_date.month)

    for source in (tour.title, tour.description):
        month = _month_from_text(source or "")
        if month:
            months.add(month)
    return months


def filter_tours(tours: list[Tour], decision: StrategyDecision) -> list[Tour]:
    result = tours
    if decision.month is not None:
        result = [tour for tour in result if decision.month in tour_months(tour)]
    return result


__all__ = [
    "SalesStrategy",
    "StrategyDecision",
    "choose_strategy",
    "detect_month",
    "filter_tours",
    "tour_months",
]
