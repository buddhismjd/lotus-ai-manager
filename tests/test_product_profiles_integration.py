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


def test_router_uses_structured_profile_before_text_analysis(monkeypatch):
    item = product(
        "Серебряные серьги",
        "Обычные серьги без упоминания ваджры.",
        (
            "https://svet-lotosa.tilda.ws/sergi/"
            "tproduct/100000000001-serebryanie-sergi"
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
            product_type="vajra",
            synonyms=("ваджра", "дордже"),
            keywords=("ваджра",),
        ),
    )

    router.reload_catalog_index()
    result = router.route_query("Есть ваджра?")

    assert result.intent == "product"
    assert result.matched_title == "Серебряные серьги"


def test_profile_entity_is_a_hard_constraint(monkeypatch):
    products = [
        product(
            "Амулет с Буддой",
            "Буддийский амулет.",
            (
                "https://svet-lotosa.tilda.ws/amulets/"
                "tproduct/100000000002-amulet-buddha"
            ),
        ),
        product(
            "Амулет Ченрезига",
            "Буддийский амулет.",
            (
                "https://svet-lotosa.tilda.ws/amulets/"
                "tproduct/100000000003-amulet-chenrezig"
            ),
        ),
    ]

    profiles = {
        "product-100000000002": ProductProfile(
            product_id="product-100000000002",
            product_type="amulet",
            primary_entity="Будда",
            entities=("Будда",),
        ),
        "product-100000000003": ProductProfile(
            product_id="product-100000000003",
            product_type="amulet",
            primary_entity="Ченрезиг",
            entities=("Ченрезиг",),
        ),
    }

    monkeypatch.setattr(
        router.ProductRepository,
        "list_all",
        lambda self: products,
    )
    monkeypatch.setattr(
        router,
        "get_product_profile",
        lambda profile_id: profiles.get(profile_id),
    )

    router.reload_catalog_index()
    result = router.route_query("Амулет Ченрезига")

    assert result.intent == "product"
    assert result.matched_title == "Амулет Ченрезига"


def test_missing_profile_falls_back_to_product_intelligence(monkeypatch):
    item = product(
        "Статуя Белой Тары",
        "Латунная статуя для домашнего алтаря.",
        (
            "https://svet-lotosa.tilda.ws/statues/"
            "tproduct/100000000004-white-tara"
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


def test_profile_lookup_failure_does_not_break_search(monkeypatch):
    item = product(
        "Амулет с Буддой",
        "Буддийский амулет.",
        (
            "https://svet-lotosa.tilda.ws/amulets/"
            "tproduct/100000000005-buddha"
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
