from __future__ import annotations

import hashlib
import re
from dataclasses import replace

from backend.catalog.product_intelligence import analyze_product
from backend.catalog.product_profiles import get_product_profile
from backend.catalog.repositories import ProductRepository, TourRepository
from backend.knowledge.aspect_registry import canonical_aspect_id
from backend.knowledge_graph.loader import load_graph
from backend.knowledge_graph.models import (
    EntityType,
    KnowledgeEntity,
    KnowledgeRelation,
    RelationType,
)
from backend.knowledge_graph.repository import KnowledgeGraphRepository
from backend.tours.intelligence import build_tour_profile
from backend.tours.planned import PLANNED_TOURS


_PRODUCT_UID_RE = re.compile(r"/tproduct/(\d+)", re.IGNORECASE)


def _copy_graph(
    source: KnowledgeGraphRepository,
) -> KnowledgeGraphRepository:
    target = KnowledgeGraphRepository()

    for entity in source.list_entities():
        target.add_entity(entity)

    for relation in source.list_relations():
        target.add_relation(relation)

    return target


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256(
        "|".join(parts).encode("utf-8")
    ).hexdigest()[:20]
    return f"{prefix}:{digest}"


def _product_entity_id(product) -> str:
    url = str(getattr(product, "url", "") or "")
    match = _PRODUCT_UID_RE.search(url)

    if match:
        return f"product:{match.group(1)}"

    return _stable_id(
        "product",
        str(getattr(product, "title", "") or ""),
        url,
    )


def _product_profile_id(product) -> str | None:
    url = str(getattr(product, "url", "") or "")
    match = _PRODUCT_UID_RE.search(url)

    if match:
        return f"product-{match.group(1)}"

    source_id = str(
        getattr(product, "source_id", "")
        or getattr(product, "id", "")
        or ""
    ).strip()

    if not source_id:
        return None

    return (
        source_id
        if source_id.startswith("product-")
        else f"product-{source_id}"
    )


def _profile_aspect_values(profile) -> tuple[str, ...]:
    if profile is None:
        return ()

    aspects = getattr(profile, "aspects", None)

    if aspects is not None:
        return tuple(aspects)

    return tuple(getattr(profile, "entities", ()) or ())


def _ensure_entity(
    repository: KnowledgeGraphRepository,
    entity: KnowledgeEntity,
) -> None:
    existing = repository.get_entity(entity.entity_id)

    if existing is None:
        repository.add_entity(entity)


def _connect_product(
    repository: KnowledgeGraphRepository,
    product,
) -> None:
    title = str(getattr(product, "title", "") or "").strip()
    url = str(getattr(product, "url", "") or "").strip()
    description = str(
        getattr(product, "description", "") or ""
    ).strip()
    category = str(getattr(product, "category", "") or "").strip()
    sku = str(getattr(product, "sku", "") or "").strip()

    if not title:
        return

    profile_id = _product_profile_id(product)
    profile = get_product_profile(profile_id) if profile_id else None

    intelligence = analyze_product(
        title=title,
        description=description,
        category=category,
        sku=sku,
    )

    product_type = (
        getattr(profile, "product_type", None)
        or intelligence.product_type
        or "unknown"
    )

    entity_id = _product_entity_id(product)
    _ensure_entity(
        repository,
        KnowledgeEntity(
            entity_id=entity_id,
            entity_type=EntityType.PRODUCT,
            name=title,
            aliases=(),
            description=description[:800],
            keywords=tuple(
                dict.fromkeys(
                    [
                        *getattr(intelligence, "keywords", ()),
                        *getattr(product, "keywords", ()),
                    ]
                )
            ),
            metadata={
                "url": url,
                "product_type": product_type,
                "source": "catalog",
            },
        ),
    )

    aspect_values = tuple(
        dict.fromkeys(
            [
                *_profile_aspect_values(profile),
                *getattr(intelligence, "entities", ()),
            ]
        )
    )

    for value in aspect_values:
        aspect_id = canonical_aspect_id(value)

        if not aspect_id:
            continue

        if repository.get_entity(aspect_id) is None:
            continue

        repository.add_relation(
            KnowledgeRelation(
                source_id=aspect_id,
                relation_type=RelationType.REPRESENTED_BY,
                target_id=entity_id,
                metadata={"source": "product_profile"},
            )
        )


def _tour_entity_id(profile) -> str:
    return f"tour:{profile.tour_id}"


def _ensure_country(
    repository: KnowledgeGraphRepository,
    country: str,
) -> str:
    existing = repository.find_by_name(country)

    for entity in existing:
        if entity.entity_type is EntityType.COUNTRY:
            return entity.entity_id

    entity_id = _stable_id("country", country)
    _ensure_entity(
        repository,
        KnowledgeEntity(
            entity_id=entity_id,
            entity_type=EntityType.COUNTRY,
            name=country,
            aliases=(),
            description="",
            keywords=(),
            metadata={"source": "tour_profile"},
        ),
    )
    return entity_id


def _ensure_place(
    repository: KnowledgeGraphRepository,
    place: str,
) -> str:
    existing = repository.find_by_name(place)

    for entity in existing:
        if entity.entity_type in {
            EntityType.PLACE,
            EntityType.REGION,
        }:
            return entity.entity_id

    entity_id = _stable_id("place", place)
    _ensure_entity(
        repository,
        KnowledgeEntity(
            entity_id=entity_id,
            entity_type=EntityType.PLACE,
            name=place,
            aliases=(),
            description="",
            keywords=(),
            metadata={"source": "tour_profile"},
        ),
    )
    return entity_id


def _ensure_practice(
    repository: KnowledgeGraphRepository,
    practice: str,
) -> str:
    existing = repository.find_by_name(practice)

    for entity in existing:
        if entity.entity_type is EntityType.PRACTICE:
            return entity.entity_id

    entity_id = _stable_id("practice", practice)
    _ensure_entity(
        repository,
        KnowledgeEntity(
            entity_id=entity_id,
            entity_type=EntityType.PRACTICE,
            name=practice.capitalize(),
            aliases=(),
            description="",
            keywords=(),
            metadata={"source": "tour_profile"},
        ),
    )
    return entity_id


def _connect_tour_profile(
    repository: KnowledgeGraphRepository,
    *,
    title: str,
    url: str,
    description: str,
    profile,
    status: str,
) -> None:
    entity_id = _tour_entity_id(profile)

    _ensure_entity(
        repository,
        KnowledgeEntity(
            entity_id=entity_id,
            entity_type=EntityType.TOUR,
            name=title,
            aliases=(),
            description=description[:1200],
            keywords=tuple(profile.keywords),
            metadata={
                "url": url,
                "status": status,
                "source": "tour_profile",
            },
        ),
    )

    for aspect in profile.aspects:
        aspect_id = canonical_aspect_id(aspect)

        if aspect_id and repository.get_entity(aspect_id):
            repository.add_relation(
                KnowledgeRelation(
                    source_id=aspect_id,
                    relation_type=RelationType.AVAILABLE_AS,
                    target_id=entity_id,
                    metadata={"status": status},
                )
            )

    country_ids = [
        _ensure_country(repository, country)
        for country in profile.countries
    ]

    for country_id in country_ids:
        repository.add_relation(
            KnowledgeRelation(
                source_id=entity_id,
                relation_type=RelationType.LOCATED_IN,
                target_id=country_id,
                metadata={"status": status},
            )
        )

    for destination in profile.destinations:
        place_id = _ensure_place(repository, destination)
        repository.add_relation(
            KnowledgeRelation(
                source_id=entity_id,
                relation_type=RelationType.ASSOCIATED_WITH,
                target_id=place_id,
                metadata={"status": status},
            )
        )

        for country_id in country_ids:
            repository.add_relation(
                KnowledgeRelation(
                    source_id=place_id,
                    relation_type=RelationType.LOCATED_IN,
                    target_id=country_id,
                    metadata={"source": "tour_profile"},
                )
            )

    for practice in profile.practices:
        practice_id = _ensure_practice(repository, practice)
        repository.add_relation(
            KnowledgeRelation(
                source_id=entity_id,
                relation_type=RelationType.INCLUDES_PRACTICE,
                target_id=practice_id,
                metadata={"status": status},
            )
        )


def _connect_active_tours(
    repository: KnowledgeGraphRepository,
) -> None:
    for tour in TourRepository().list_all():
        profile = build_tour_profile(tour)

        _connect_tour_profile(
            repository,
            title=str(getattr(tour, "title", "") or profile.tour_id),
            url=str(getattr(tour, "url", "") or ""),
            description=str(getattr(tour, "description", "") or ""),
            profile=profile,
            status="active",
        )


def _connect_planned_tours(
    repository: KnowledgeGraphRepository,
) -> None:
    for planned in PLANNED_TOURS:
        profile = type(
            "PlannedTourProfile",
            (),
            {
                "tour_id": f"planned-{planned.slug}",
                "countries": planned.countries,
                "destinations": planned.destinations,
                "aspects": planned.aspects,
                "practices": planned.practices,
                "keywords": tuple(
                    dict.fromkeys(
                        [
                            *planned.countries,
                            *planned.destinations,
                            *planned.aspects,
                            *planned.practices,
                        ]
                    )
                ),
            },
        )()

        _connect_tour_profile(
            repository,
            title=planned.title,
            url="",
            description=planned.note,
            profile=profile,
            status=planned.status,
        )


def build_runtime_graph(
    *,
    include_products: bool = True,
    include_active_tours: bool = True,
    include_planned_tours: bool = True,
) -> KnowledgeGraphRepository:
    repository = _copy_graph(load_graph())

    if include_products:
        for product in ProductRepository().list_all():
            _connect_product(repository, product)

    if include_active_tours:
        _connect_active_tours(repository)

    if include_planned_tours:
        _connect_planned_tours(repository)

    return repository


__all__ = ["build_runtime_graph"]
