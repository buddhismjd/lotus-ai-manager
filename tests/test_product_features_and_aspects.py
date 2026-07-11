from types import SimpleNamespace

import pytest

import backend.rag.dynamic_query_router as router
from backend.catalog.product_features import (
    extract_dimensions_cm,
    extract_point_counts,
)
from backend.catalog.product_profiles import ProductProfile


def product(title: str, description: str, url: str):
    return SimpleNamespace(
        title=title,
        description=description,
        url=url,
        category="",
        material="",
        keywords=[],
        sku="",
    )


def test_extracts_dimensions_and_point_counts() -> None:
    assert extract_dimensions_cm("Высота 40 см.") == (40.0,)
    assert extract_point_counts("Восьмиконечная ваджра") == (8,)


def test_profile_uses_aspect_terminology() -> None:
    profile = ProductProfile(
        product_id="product-1",
        primary_entity="Белая Тара",
        entities=("Белая Тара",),
    )

    assert profile.primary_aspect == "Белая Тара"
    assert profile.aspects == ("Белая Тара",)
    assert "Основной аспект: Белая Тара" in profile.to_search_text()
    assert "Аспекты: Белая Тара" in profile.to_search_text()


def test_dimension_query_prefers_40cm_buddha(monkeypatch) -> None:
    products = [
        product(
            "Cтатуя Будды Амитабхи",
            "Медная статуя Будды.",
            "https://example.com/tproduct/1-amitabha",
        ),
        product(
            "Статуя Будды Шакьямуни",
            "Высота 40 см. Бронзовая статуя Будды.",
            "https://example.com/tproduct/2-shakyamuni",
        ),
    ]

    monkeypatch.setattr(
        router.ProductRepository,
        "list_all",
        lambda self: products,
    )
    monkeypatch.setattr(
        router.TourRepository,
        "list_all",
        lambda self: [],
    )
    monkeypatch.setattr(
        router,
        "get_product_profile",
        lambda profile_id: None,
    )

    router.reload_catalog_index()
    result = router.route_query(
        "Ищу статую Будду около 45 см."
    )

    assert result.matched_title == "Статуя Будды Шакьямуни"


def test_unspecified_eight_point_vajra_gets_note(monkeypatch) -> None:
    item = product(
        "Ваджра",
        "Ритуальный предмет для практики.",
        "https://example.com/tproduct/3-vajra",
    )

    monkeypatch.setattr(
        router.ProductRepository,
        "list_all",
        lambda self: [item],
    )
    monkeypatch.setattr(
        router.TourRepository,
        "list_all",
        lambda self: [],
    )
    monkeypatch.setattr(
        router,
        "get_product_profile",
        lambda profile_id: ProductProfile(
            product_id=profile_id,
            product_type="vajra",
        ),
    )

    router.reload_catalog_index()
    result = router.route_query(
        "Восьмиконечная вадра нужна"
    )

    assert result.matched_title == "Ваджра"
    assert "не указано" in (result.matched_note or "")


def test_aspect_query_contains_different_product_variants(monkeypatch) -> None:
    products = [
        product(
            "Статуя Дзамбалы",
            "Статуя аспекта Дзамбала.",
            "https://example.com/tproduct/4-statue",
        ),
        product(
            'Обсидиановый амулет "Дзамбала"',
            "Амулет аспекта Дзамбала.",
            "https://example.com/tproduct/5-amulet",
        ),
    ]

    profiles = {
        "product-4": ProductProfile(
            product_id="product-4",
            product_type="statue",
            primary_entity="Дзамбала",
            entities=("Дзамбала",),
        ),
        "product-5": ProductProfile(
            product_id="product-5",
            product_type="amulet",
            primary_entity="Дзамбала",
            entities=("Дзамбала",),
        ),
    }

    monkeypatch.setattr(
        router.ProductRepository,
        "list_all",
        lambda self: products,
    )
    monkeypatch.setattr(
        router.TourRepository,
        "list_all",
        lambda self: [],
    )
    monkeypatch.setattr(
        router,
        "get_product_profile",
        lambda profile_id: profiles.get(profile_id),
    )

    router.reload_catalog_index()
    result = router.route_query("У Вас есть Дзамбала?")

    titles = {title for title, _ in result.alternatives}

    assert "Статуя Дзамбалы" in titles
    assert 'Обсидиановый амулет "Дзамбала"' in titles
