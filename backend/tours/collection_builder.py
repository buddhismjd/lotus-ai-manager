from __future__ import annotations

import re
from urllib.parse import quote

from backend.catalog.collection_builder import CollectionItem, _price
from backend.catalog.collection_ranking import rank_collection
from backend.structured_catalog.models import StructuredTour
from backend.structured_catalog.repositories import StructuredTourRepository
from backend.tours.intelligence import COUNTRY_PATTERNS, normalize
from backend.tours.planned import PLANNED_TOURS


_NAVIGATION_LINES = {
    "путешествия",
    "магазин",
    "психолог-буддолог",
    "психолог буддолог",
    "отзывы",
    "связаться с нами",
    "контакты",
}


def clean_tour_description(value: str | None) -> str | None:
    """Remove Tilda navigation/footer noise while preserving tour copy."""
    if not value:
        return None

    cleaned_lines: list[str] = []
    seen: set[str] = set()
    for raw_line in re.split(r"[\r\n]+", value):
        line = " ".join(raw_line.split()).strip(" •|—-")
        if not line:
            continue
        normalized = normalize(line).strip(" .:;!?—-")
        if normalized in _NAVIGATION_LINES:
            continue
        if normalized.startswith("©") or normalized.startswith("политика конфиденциальности"):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned_lines.append(line)

    result = " ".join(cleaned_lines).strip()
    return result or None


_QUERY_COUNTRY_ALIASES = {
    "Тибет": ("тибет", "тибетск"),
    "Индия": ("индия", "индии", "индийск"),
    "Бутан": ("бутан", "бутане", "бутанск"),
    "Непал": ("непал", "непале", "непальск"),
    "Япония": ("япония", "японии", "японск"),
    "Монголия": ("монгол",),
    "Россия": ("росси", "алтай", "белух"),
}


def detect_country(query: str) -> str | None:
    text = normalize(query)
    for country, aliases in _QUERY_COUNTRY_ALIASES.items():
        if any(normalize(alias) in text for alias in aliases):
            return country
    return None


def _tour_image(tour: StructuredTour) -> str | None:
    for key in ("image_url", "hero_image", "cover_image", "og_image"):
        value = tour.metadata.get(key) if tour.metadata else None
        if value:
            return str(value)
    if tour.url:
        return f"/api/sales/page-image?source={quote(tour.url, safe='')}"
    return None


def _published_item(tour: StructuredTour) -> CollectionItem:
    date_text = tour.schedule.source_text if tour.schedule else None
    material = ", ".join(tour.countries) if tour.countries else None
    return CollectionItem(
        id=tour.id,
        title=tour.title,
        url=tour.url or None,
        availability=date_text,
        material=material,
        size=None,
        status=tour.status,
        image_url=_tour_image(tour),
        price=(
            f"от {_price(tour.price, tour.currency)}"
            if tour.price is not None and tour.metadata.get("price_is_from")
            else _price(tour.price, tour.currency)
        ),
        description=clean_tour_description(tour.description),
        button_label="Открыть тур",
        group="Туры по направлению",
        item_type="tour",
    )


def build_tour_collection(query: str) -> list[CollectionItem]:
    country = detect_country(query)
    if not country:
        return []

    published = []
    for tour in StructuredTourRepository().list_all():
        countries = set(tour.countries)
        if not countries:
            searchable = " ".join([tour.title, tour.description, tour.url or ""])
            detected = next((
                label for label, aliases in COUNTRY_PATTERNS.items()
                if any(normalize(alias) in normalize(searchable) for alias in aliases)
            ), None)
            if detected:
                countries.add(detected)
        if country in countries:
            published.append(tour)
    if published:
        return rank_collection(query, [_published_item(tour) for tour in published])

    return rank_collection(query, [
        CollectionItem(
            id=f"planned-{tour.slug}",
            title=tour.title,
            url=None,
            availability=tour.note,
            material=", ".join(tour.countries),
            status="planned",
            description=tour.note,
            button_label="Подробнее",
            group="Готовящиеся путешествия",
            item_type="tour",
        )
        for tour in PLANNED_TOURS
        if country in tour.countries
    ])


__all__ = ["build_tour_collection", "clean_tour_description", "detect_country"]
