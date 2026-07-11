from types import SimpleNamespace

import pytest

import backend.rag.dynamic_query_router as router
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


@pytest.fixture(autouse=True)
def empty_tours(monkeypatch):
    monkeypatch.setattr(
        router.TourRepository,
        "list_all",
        lambda self: [],
    )
    router.reload_catalog_index()
    yield
    router.reload_catalog_index()


def test_profile_is_used_when_available(monkeypatch):
    item = product(
        "Амулет Ченрезига",
        "Буддийский предмет.",
        (
            "https://svet-lotosa.tilda.ws/amulets/"
            "tproduct/100000000001-chenrezig"
        ),
    )

    monkeypatch.setattr(
        router.ProductRepository,
        "list_all",
        lambda self: [item],
    )
    monkeypatch.setattr(
        router,
        "get_product_profile",
        lambda profile_id: ProductProfile(
            product_id=profile_id,
            product_type="amulet",
            primary_entity="Ченрезиг",
            entities=("Ченрезиг",),
            usages=("protection",),
            synonyms=("амулет", "оберег"),
        ),
    )

    router.reload_catalog_index()
    result = router.route_query("Амулет Ченрезига")

    assert result.intent == "product"
    assert result.matched_title == "Амулет Ченрезига"


def test_missing_profile_uses_product_intelligence(monkeypatch):
    item = product(
        "Статуя Белой Тары",
        "Латунная статуя для домашнего алтаря.",
        (
            "https://svet-lotosa.tilda.ws/statues/"
            "tproduct/100000000002-white-tara"
        ),
    )

    monkeypatch.setattr(
        router.ProductRepository,
        "list_all",
        lambda self: [item],
    )
    monkeypatch.setattr(
        router,
        "get_product_profile",
        lambda profile_id: None,
    )

    router.reload_catalog_index()
    result = router.route_query("Статуя Белой Тары")

    assert result.intent == "product"
    assert result.matched_title == "Статуя Белой Тары"


def test_profile_database_error_does_not_break_search(monkeypatch):
    item = product(
        "Амулет с Буддой",
        "Буддийский амулет.",
        (
            "https://svet-lotosa.tilda.ws/amulets/"
            "tproduct/100000000003-buddha"
        ),
    )

    monkeypatch.setattr(
        router.ProductRepository,
        "list_all",
        lambda self: [item],
    )

    def fail(_profile_id):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(router, "get_product_profile", fail)

    router.reload_catalog_index()
    result = router.route_query("Амулет Будды")

    assert result.intent == "product"
    assert result.matched_title == "Амулет с Буддой"


def test_jewelry_with_dorje_is_not_classified_as_vajra():
    intelligence = router.analyze_product(
        title="Серебряные серьги",
        description="Украшены символом двойного дордже.",
    )

    assert intelligence.product_type == "jewelry"


def test_real_vajra_is_classified_as_vajra():
    intelligence = router.analyze_product(
        title="Ваджра пятиконечная",
        description="Ритуальный предмет для практики.",
    )

    assert intelligence.product_type == "vajra"
