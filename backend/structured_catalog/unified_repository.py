from __future__ import annotations

from collections.abc import Iterable

from backend.catalog.product_profiles import get_product_profile
from backend.catalog.repositories import (
    ConsultationRepository,
    ProductRepository,
)
from backend.structured_catalog.contract import (
    CatalogItem,
    CatalogItemType,
    CatalogQuery,
    UnifiedCatalogContract,
)
from backend.structured_catalog.models import (
    StructuredProduct,
    StructuredService,
    StructuredTour,
)
from backend.structured_catalog.repositories import StructuredTourRepository


def _clean(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value.strip() for value in values if value.strip()))


def _product_item(product) -> CatalogItem:
    profile = get_product_profile(product.id)
    materials = profile.materials if profile else (() if not product.material else (product.material,))
    aspects = profile.aspects if profile else ()
    usages = profile.usages if profile else ()
    tags = _clean(
        (
            product.category or "",
            *(profile.keywords if profile else ()),
            *aspects,
            *materials,
            *usages,
        )
    )
    structured = StructuredProduct(
        id=product.id,
        title=product.title,
        url=product.url,
        description=product.description,
        status="published" if product.available else "unavailable",
        category=product.category,
        price=product.price,
        currency=product.currency,
        available=product.available,
        materials=materials,
        aspects=aspects,
        keywords=profile.keywords if profile else tuple(product.keywords),
        metadata=dict(product.metadata),
    )
    return CatalogItem(
        id=structured.id,
        item_type=CatalogItemType.PRODUCT,
        title=structured.title,
        url=structured.url,
        summary=structured.description,
        status=structured.status,
        tags=tags,
        price=structured.price,
        currency=structured.currency,
        attributes={
            "category": structured.category,
            "available": structured.available,
            "materials": structured.materials,
            "aspects": structured.aspects,
            "usages": usages,
        },
    )


def _tour_item(tour: StructuredTour) -> CatalogItem:
    tags = _clean(
        (
            *tour.countries,
            *tour.regions,
            *tour.destinations,
            *tour.aspects,
            *tour.keywords,
        )
    )
    schedule = None
    if tour.schedule is not None:
        schedule = {
            "start_day": tour.schedule.start_day,
            "start_month": tour.schedule.start_month,
            "end_day": tour.schedule.end_day,
            "end_month": tour.schedule.end_month,
            "year": tour.schedule.year,
            "source_text": tour.schedule.source_text,
        }
    return CatalogItem(
        id=tour.id,
        item_type=CatalogItemType.TOUR,
        title=tour.title,
        url=tour.url,
        summary=tour.description,
        status=tour.status,
        tags=tags,
        price=tour.price,
        currency=tour.currency,
        attributes={
            "schedule": schedule,
            "duration_days": tour.duration_days,
            "countries": tour.countries,
            "regions": tour.regions,
            "destinations": tour.destinations,
            "difficulty": tour.difficulty,
        },
    )


def _service_item(service) -> CatalogItem:
    structured = StructuredService(
        id=service.id,
        title=service.title,
        url=service.url,
        description=service.description,
        status="published",
        specialist=service.specialist,
        duration_minutes=service.duration_minutes,
        price=service.price,
        currency=service.currency,
        topics=tuple(service.topics),
        booking_url=service.url,
        metadata=dict(service.metadata),
    )
    return CatalogItem(
        id=structured.id,
        item_type=CatalogItemType.PSYCHOLOGIST_SERVICE,
        title=structured.title,
        url=structured.url,
        summary=structured.description,
        status=structured.status,
        tags=_clean(structured.topics),
        price=structured.price,
        currency=structured.currency,
        attributes={
            "specialist": structured.specialist,
            "duration_minutes": structured.duration_minutes,
            "topics": structured.topics,
            "booking_url": structured.booking_url,
        },
    )


class UnifiedCatalogRepository(UnifiedCatalogContract):
    """Single commercial catalog over products, tours and psychologist service."""

    def __init__(
        self,
        products: ProductRepository | None = None,
        tours: StructuredTourRepository | None = None,
        services: ConsultationRepository | None = None,
    ) -> None:
        self._products = products or ProductRepository()
        self._tours = tours or StructuredTourRepository()
        self._services = services or ConsultationRepository()

    def get_item(
        self,
        item_type: CatalogItemType,
        item_id: str,
    ) -> CatalogItem | None:
        if item_type is CatalogItemType.PRODUCT:
            value = self._products.get_by_id(item_id)
            return _product_item(value) if value else None
        if item_type is CatalogItemType.TOUR:
            value = self._tours.get_by_id(item_id)
            return _tour_item(value) if value else None
        if item_type is CatalogItemType.PSYCHOLOGIST_SERVICE:
            value = self._services.get_by_id(item_id)
            return _service_item(value) if value else None
        raise ValueError(f"Unsupported catalog item type: {item_type}")

    def list_items(
        self,
        query: CatalogQuery | None = None,
    ) -> list[CatalogItem]:
        query = query or CatalogQuery()
        item_types = query.item_types or tuple(CatalogItemType)
        result: list[CatalogItem] = []

        if CatalogItemType.PRODUCT in item_types:
            result.extend(_product_item(item) for item in self._products.list_all(query.published_only))
        if CatalogItemType.TOUR in item_types:
            result.extend(_tour_item(item) for item in self._tours.list_all(query.published_only))
        if CatalogItemType.PSYCHOLOGIST_SERVICE in item_types:
            result.extend(_service_item(item) for item in self._services.list_all(query.published_only))

        filtered = self._filter(result, query)
        return filtered[: query.limit]

    def search(self, query: CatalogQuery) -> list[CatalogItem]:
        return self.list_items(query)

    def recommendation_candidates(
        self,
        source: CatalogItem,
        *,
        limit: int = 10,
    ) -> list[CatalogItem]:
        if limit < 1 or limit > 100:
            raise ValueError("Recommendation limit must be between 1 and 100")

        # Recommendations never leave the commercial catalog boundary.
        candidates = self.list_items(
            CatalogQuery(
                item_types=(source.item_type,),
                published_only=True,
                limit=100,
            )
        )
        source_tags = {tag.casefold() for tag in source.tags}

        scored: list[tuple[int, CatalogItem]] = []
        for candidate in candidates:
            if candidate.id == source.id:
                continue
            overlap = len(source_tags & {tag.casefold() for tag in candidate.tags})
            if overlap:
                scored.append((overlap, candidate))

        scored.sort(key=lambda pair: (-pair[0], pair[1].title.casefold()))
        return [candidate for _, candidate in scored[:limit]]

    @staticmethod
    def _filter(items: list[CatalogItem], query: CatalogQuery) -> list[CatalogItem]:
        text = query.text.strip().casefold()
        required_tags = {tag.casefold() for tag in query.tags if tag.strip()}
        result: list[CatalogItem] = []

        for item in items:
            if query.published_only and item.status != "published":
                continue
            item_tags = {tag.casefold() for tag in item.tags}
            if required_tags and not required_tags.issubset(item_tags):
                continue
            if text:
                haystack = " ".join((item.title, item.summary, *item.tags)).casefold()
                if text not in haystack:
                    continue
            result.append(item)

        return sorted(result, key=lambda item: (item.item_type.value, item.title.casefold()))
