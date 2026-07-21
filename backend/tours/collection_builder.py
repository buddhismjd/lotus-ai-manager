from __future__ import annotations

from dataclasses import asdict
from typing import Any

from backend.catalog.collection_builder import CollectionItem
from backend.structured_catalog.models import StructuredTour
from backend.structured_catalog.repositories import StructuredTourRepository
from backend.tours.intelligence import COUNTRY_PATTERNS, normalize
from backend.tours.planned import PLANNED_TOURS


def detect_country(query: str) -> str | None:
    text = normalize(query)
    for country, aliases in COUNTRY_PATTERNS.items():
        if any(normalize(alias) in text for alias in aliases):
            return country
    return None


def _published_item(tour: StructuredTour) -> CollectionItem:
    date_text = tour.schedule.source_text if tour.schedule else None
    size = f"{tour.duration_days} дней" if tour.duration_days else None
    material = ", ".join(tour.countries) if tour.countries else None
    return CollectionItem(
        id=tour.id,
        title=tour.title,
        url=tour.url or None,
        availability=date_text,
        material=material,
        size=size,
        status=tour.status,
    )


def build_tour_collection(query: str) -> list[CollectionItem]:
    country = detect_country(query)
    if not country:
        return []

    published = [
        tour for tour in StructuredTourRepository().list_all()
        if country in tour.countries
    ]
    if published:
        return [_published_item(tour) for tour in published]

    return [
        CollectionItem(
            id=f"planned-{tour.slug}",
            title=tour.title,
            url=None,
            availability=tour.note,
            material=", ".join(tour.countries),
            status="planned",
        )
        for tour in PLANNED_TOURS
        if country in tour.countries
    ]


__all__ = ["build_tour_collection", "detect_country"]
