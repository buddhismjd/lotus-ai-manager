from types import SimpleNamespace

import backend.catalog.aspect_catalog as aspects
from backend.catalog.product_profiles import ProductProfile


def product(title: str, url: str):
    return SimpleNamespace(
        title=title,
        url=url,
        source_id="",
        id="",
    )


def test_groups_different_product_types_by_aspect(monkeypatch) -> None:
    products = [
        product(
            "Статуя Дзамбалы",
            "https://example.com/tproduct/100-statue",
        ),
        product(
            'Амулет "Дзамбала"',
            "https://example.com/tproduct/200-amulet",
        ),
    ]

    profiles = {
        "product-100": ProductProfile(
            product_id="product-100",
            product_type="statue",
            primary_entity="Дзамбала",
            entities=("Дзамбала",),
        ),
        "product-200": ProductProfile(
            product_id="product-200",
            product_type="amulet",
            primary_entity="Дзамбала",
            entities=("Дзамбала",),
        ),
    }

    monkeypatch.setattr(
        aspects.ProductRepository,
        "list_all",
        lambda self: products,
    )
    monkeypatch.setattr(
        aspects,
        "get_product_profile",
        lambda profile_id: profiles.get(profile_id),
    )

    index = aspects.build_aspect_index()
    group = aspects.find_aspect_group(
        "Дзамбала",
        index=index,
    )

    assert group is not None
    assert set(group.by_type) == {
        "Статуи",
        "Амулеты",
    }


def test_response_uses_aspect_terminology(monkeypatch) -> None:
    products = [
        product(
            "Статуя Белой Тары",
            "https://example.com/tproduct/300-statue",
        ),
    ]
    profile = ProductProfile(
        product_id="product-300",
        product_type="statue",
        primary_entity="Белая Тара",
        entities=("Белая Тара",),
    )

    monkeypatch.setattr(
        aspects.ProductRepository,
        "list_all",
        lambda self: products,
    )
    monkeypatch.setattr(
        aspects,
        "get_product_profile",
        lambda profile_id: profile,
    )

    group = aspects.find_aspect_group("Белая Тара")

    assert group is not None
    response = aspects.format_aspect_response(group)

    assert "По аспекту «Белая Тара»" in response
    assert "Статуи — 1" in response


def test_products_are_deduplicated_by_url(monkeypatch) -> None:
    duplicate = product(
        "Статуя Дзамбалы",
        "https://example.com/tproduct/400-statue",
    )
    profile = ProductProfile(
        product_id="product-400",
        product_type="statue",
        entities=("Дзамбала",),
    )

    monkeypatch.setattr(
        aspects.ProductRepository,
        "list_all",
        lambda self: [duplicate, duplicate],
    )
    monkeypatch.setattr(
        aspects,
        "get_product_profile",
        lambda profile_id: profile,
    )

    group = aspects.find_aspect_group("Дзамбала")

    assert group is not None
    assert len(group.products) == 1
