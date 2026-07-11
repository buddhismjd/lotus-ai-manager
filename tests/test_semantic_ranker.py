from types import SimpleNamespace

import pytest

import backend.rag.dynamic_query_router as router


def product(
    title: str,
    description: str,
    url: str,
    category: str = "",
):
    return SimpleNamespace(
        title=title,
        description=description,
        url=url,
        category=category,
        material="",
        keywords=[],
        sku="",
    )


@pytest.fixture(autouse=True)
def catalog(monkeypatch):
    monkeypatch.setattr(
        router.ProductRepository,
        "list_all",
        lambda self: [
            product(
                "Серебряное гау с двойным дордже",
                "Серебряный амулет-гау с символом двойного дордже.",
                "https://example.com/gau",
            ),
            product(
                "Ваджра пятиконечная",
                "Ритуальная ваджра для ежедневной практики.",
                "https://example.com/vajra",
            ),
            product(
                "Железный амулет Пхурба Дордже",
                "Защитный амулет для практики.",
                "https://example.com/protective-amulet",
            ),
            product(
                "Амулет Ченрезига",
                "Амулет с образом Ченрезига.",
                "https://example.com/chenrezig",
            ),
            product(
                "Амулет с Буддой",
                "Амулет с образом Будды.",
                "https://example.com/buddha-amulet",
            ),
            product(
                "Статуя Белой Тары",
                "Латунная статуя для домашнего алтаря.",
                "https://example.com/white-tara",
            ),
        ],
    )
    monkeypatch.setattr(
        router.TourRepository,
        "list_all",
        lambda self: [],
    )
    router.reload_catalog_index()
    yield
    router.reload_catalog_index()


def test_vajra_query_prefers_actual_vajra_over_gau():
    result = router.route_query("Есть ваджра?")

    assert result.intent == "product"
    assert result.matched_title == "Ваджра пятиконечная"


def test_protective_amulet_uses_usage_and_kind():
    result = router.route_query("Хочу защитный амулет")

    assert result.intent == "product"
    assert result.matched_title == "Железный амулет Пхурба Дордже"


def test_entity_and_kind_are_combined():
    result = router.route_query("Амулет Ченрезига")

    assert result.intent == "product"
    assert result.matched_title == "Амулет Ченрезига"


def test_unknown_entity_is_not_replaced():
    result = router.route_query("Амулет Зеленой Тары")

    assert result.intent == "product"
    assert result.matched_title is None


def test_material_entity_and_type_can_rank_together():
    result = router.route_query("Латунная статуя Белой Тары")

    assert result.intent == "product"
    assert result.matched_title == "Статуя Белой Тары"
