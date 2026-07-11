from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlannedTour:
    slug: str
    title: str
    countries: tuple[str, ...]
    destinations: tuple[str, ...]
    aspects: tuple[str, ...] = ()
    practices: tuple[str, ...] = ()
    status: str = "planned"
    note: str = ""


PLANNED_TOURS: tuple[PlannedTour, ...] = (
    PlannedTour(
        slug="nepal-lapchi",
        title="Непал — Лапчи, место силы Миларепы",
        countries=("Непал",),
        destinations=("Лапчи",),
        aspects=("Миларепа",),
        practices=("паломничество", "поход", "медитация"),
        status="planned",
        note=(
            "Программа находится в подготовке. "
            "Даты и страница тура пока не опубликованы."
        ),
    ),
)


def normalize(value: str | None) -> str:
    return (value or "").lower().replace("ё", "е")


def find_planned_tour(query: str) -> PlannedTour | None:
    normalized = normalize(query)

    best_score = 0
    best: PlannedTour | None = None

    for tour in PLANNED_TOURS:
        score = 0

        for country in tour.countries:
            if normalize(country) in normalized:
                score += 3

        for destination in tour.destinations:
            if normalize(destination) in normalized:
                score += 5

        for aspect in tour.aspects:
            if normalize(aspect) in normalized:
                score += 4

        for practice in tour.practices:
            if normalize(practice) in normalized:
                score += 1

        if score > best_score:
            best_score = score
            best = tour

    return best if best_score >= 3 else None


__all__ = [
    "PLANNED_TOURS",
    "PlannedTour",
    "find_planned_tour",
]
