from types import SimpleNamespace

import backend.services.bodhi_service as service
from backend.catalog.aspect_catalog import (
    AspectGroup,
    AspectProduct,
)
from backend.rag.dynamic_query_router import Route


def test_general_aspect_query_returns_grouped_products(monkeypatch):
    group = AspectGroup(
        aspect="Дзамбала",
        products=(
            AspectProduct(
                title="Статуя Дзамбалы",
                url="https://example.com/statue",
                product_type="statue",
                product_type_label="Статуи",
            ),
            AspectProduct(
                title='Амулет "Дзамбала"',
                url="https://example.com/amulet",
                product_type="amulet",
                product_type_label="Амулеты",
            ),
        ),
    )

    monkeypatch.setattr(
        service,
        "find_aspect_group",
        lambda aspect: group,
    )

    response = service.answer_query("У Вас есть Дзамбала?")

    assert response.kind == "product"
    assert "По аспекту" in response.text
    assert "Статуи — 1" in response.text
    assert "Амулеты — 1" in response.text


def test_specific_product_query_does_not_expand_aspect(monkeypatch):
    product = SimpleNamespace(
        title="Статуя Белой Тары",
        description="Латунная статуя.",
        url="https://example.com/tproduct/100-white-tara",
        category="Статуи",
        sku="",
    )

    monkeypatch.setattr(
        service,
        "route_query",
        lambda query: Route(
            intent="product",
            confidence=0.99,
            reason="test",
            matched_title=product.title,
            matched_url=product.url,
        ),
    )
    monkeypatch.setattr(
        service.ProductRepository,
        "list_all",
        lambda self: [product],
    )
    monkeypatch.setattr(
        service,
        "get_product_profile",
        lambda profile_id: None,
    )

    response = service.answer_query("Статуя Белой Тары")

    assert response.title == "Статуя Белой Тары"
    assert "разные виды товаров" not in response.text


def test_route_note_is_shown(monkeypatch):
    product = SimpleNamespace(
        title="Ваджра",
        description="Ритуальный предмет.",
        url="https://example.com/tproduct/200-vajra",
        category="",
        sku="",
    )

    monkeypatch.setattr(
        service,
        "route_query",
        lambda query: Route(
            intent="product",
            confidence=0.85,
            reason="test",
            matched_title=product.title,
            matched_url=product.url,
            matched_note=(
                "В описании товара не указано, "
                "что он 8-конечный."
            ),
        ),
    )
    monkeypatch.setattr(
        service.ProductRepository,
        "list_all",
        lambda self: [product],
    )
    monkeypatch.setattr(
        service,
        "get_product_profile",
        lambda profile_id: None,
    )

    response = service.answer_query("Восьмиконечная вадра нужна")

    assert "не указано" in response.text


def test_missing_description_produces_recommendation(monkeypatch):
    product = SimpleNamespace(
        title="Статуя Гаруды",
        description="",
        url="https://example.com/tproduct/300-garuda",
        category="Статуи",
        sku="",
    )

    monkeypatch.setattr(
        service,
        "route_query",
        lambda query: Route(
            intent="product",
            confidence=0.99,
            reason="test",
            matched_title=product.title,
            matched_url=product.url,
        ),
    )
    monkeypatch.setattr(
        service.ProductRepository,
        "list_all",
        lambda self: [product],
    )
    monkeypatch.setattr(
        service,
        "get_product_profile",
        lambda profile_id: None,
    )

    response = service.answer_query("Статуя Гаруды")

    assert "нет подробного описания" in response.text
    assert "высоту" in response.text
