from __future__ import annotations

from dataclasses import replace

import pytest

from backend.structured_catalog.contract import (
    ALLOWED_CATALOG_ITEM_TYPES,
    CatalogItem,
    CatalogItemType,
    CatalogQuery,
    UnifiedCatalogContract,
)
from backend.structured_catalog.unified_repository import UnifiedCatalogRepository


def test_contract_has_strict_commercial_boundary() -> None:
    assert ALLOWED_CATALOG_ITEM_TYPES == {
        CatalogItemType.PRODUCT,
        CatalogItemType.TOUR,
        CatalogItemType.PSYCHOLOGIST_SERVICE,
    }
    assert {item.value for item in ALLOWED_CATALOG_ITEM_TYPES} == {
        "product",
        "tour",
        "psychologist_service",
    }


def test_catalog_item_rejects_unsupported_type() -> None:
    with pytest.raises(ValueError):
        CatalogItem(
            id="practice-vajra",
            item_type="practice",  # type: ignore[arg-type]
            title="Практика Ваджры",
            url="https://example.test/practice",
        )


def test_repository_implements_contract() -> None:
    assert isinstance(UnifiedCatalogRepository(), UnifiedCatalogContract)


def test_query_rejects_out_of_boundary_type() -> None:
    with pytest.raises(ValueError):
        CatalogQuery(item_types=("book",))  # type: ignore[arg-type]


def test_repository_returns_only_supported_types() -> None:
    repository = UnifiedCatalogRepository()
    items = repository.list_items(CatalogQuery(limit=100))

    assert items
    assert {item.item_type for item in items} <= ALLOWED_CATALOG_ITEM_TYPES


def test_tour_catalog_is_available_through_unified_contract() -> None:
    repository = UnifiedCatalogRepository()
    tours = repository.search(
        CatalogQuery(item_types=(CatalogItemType.TOUR,), text="Кайлас")
    )

    assert tours
    assert all(item.item_type is CatalogItemType.TOUR for item in tours)


def test_recommendations_never_cross_domain_boundary() -> None:
    repository = UnifiedCatalogRepository()
    products = repository.list_items(
        CatalogQuery(item_types=(CatalogItemType.PRODUCT,), limit=100)
    )
    source = products[0]
    recommendations = repository.recommendation_candidates(source)

    assert all(item.item_type is CatalogItemType.PRODUCT for item in recommendations)
    assert all(item.id != source.id for item in recommendations)


def test_recommendation_source_cannot_be_changed_to_unsupported_type() -> None:
    source = CatalogItem(
        id="product-1",
        item_type=CatalogItemType.PRODUCT,
        title="Ваджра",
        url="https://example.test/product-1",
    )

    with pytest.raises(ValueError):
        replace(source, item_type="practice")  # type: ignore[arg-type]
