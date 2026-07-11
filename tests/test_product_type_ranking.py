from types import SimpleNamespace

import backend.rag.dynamic_query_router as router


def _product(title: str, category: str, description: str, url: str):
    return SimpleNamespace(
        title=title,
        category=category,
        description=description,
        material="",
        keywords=[],
        url=url,
    )


def _install_catalog(monkeypatch) -> None:
    monkeypatch.setattr(
        router.ProductRepository,
        "list_all",
        lambda self: [
            _product(
                "Амулет с Буддой",
                "Подвески",
                "Амулет с изображением Будды",
                "https://example.com/amulet",
            ),
            _product(
                "Статуя Будды Шакьямуни",
                "Статуи",
                "Буддийская статуя для домашнего алтаря",
                "https://example.com/statue",
            ),
        ],
    )
    monkeypatch.setattr(
        router.TourRepository,
        "list_all",
        lambda self: [],
    )
    router.reload_catalog_index()


def test_product_kind_understands_russian_cases() -> None:
    assert router.detect_product_kind("статуя Будды") == "statue"
    assert router.detect_product_kind("хочу статую Будды") == "statue"
    assert router.detect_product_kind("каталог статуй") == "statue"
    assert router.detect_product_kind("о статуе Будды") == "statue"
    assert router.detect_product_kind("амулет с Буддой") == "amulet"


def test_statue_query_does_not_return_amulet(monkeypatch) -> None:
    _install_catalog(monkeypatch)

    result = router.route_query("Хочу статую Будды")

    assert result.intent == "product"
    assert result.matched_title == "Статуя Будды Шакьямуни"


def test_amulet_query_does_not_return_statue(monkeypatch) -> None:
    _install_catalog(monkeypatch)

    result = router.route_query("Хочу амулет с Буддой")

    assert result.intent == "product"
    assert result.matched_title == "Амулет с Буддой"
