from types import SimpleNamespace

import pytest

import backend.rag.dynamic_query_router as router


def product(title, category, description, url):
    return SimpleNamespace(
        title=title,
        category=category,
        description=description,
        material="",
        keywords=[],
        url=url,
    )


def tour(title, country, region, description, url):
    return SimpleNamespace(
        title=title,
        country=country,
        region=region,
        description=description,
        difficulty="",
        guide="",
        keywords=[],
        url=url,
    )


@pytest.fixture(autouse=True)
def catalog(monkeypatch):
    monkeypatch.setattr(
        router.ProductRepository,
        "list_all",
        lambda self: [
            product(
                "Амулет с Буддой",
                "Подвески",
                "Амулет с изображением Будды",
                "https://example.com/amulet",
            ),
            product(
                "Статуя Будды Шакьямуни",
                "Статуи",
                "Статуя Будды для домашнего алтаря",
                "https://example.com/statue",
            ),
            product(
                "Коралловые чётки",
                "Чётки",
                "Мала для практики",
                "https://example.com/mala",
            ),
            product(
                "Ваджра пятиконечная",
                "Ритуальные предметы",
                "Дордже для практики",
                "https://example.com/vajra",
            ),
            product(
                "Тханка Зеленой Тары",
                "Тханки",
                "Буддийская танка",
                "https://example.com/thangka",
            ),
            product(
                "Поющая чаша",
                "Поющие чаши",
                "Чаша для медитации",
                "https://example.com/bowl",
            ),
            product(
                "Браслет из Непала",
                "Браслеты",
                "Товар из Непала",
                "https://example.com/nepal-product",
            ),
        ],
    )
    monkeypatch.setattr(
        router.TourRepository,
        "list_all",
        lambda self: [
            tour(
                "Тибет + Кайлас — 18 дней",
                "Китай",
                "Тибет",
                "Паломничество к Кайласу",
                "https://example.com/kailash",
            ),
            tour(
                "Лапчи — место силы Миларепы",
                "Непал",
                "Лапчи",
                "Паломнический поход в Лапчи",
                "https://example.com/lapchi",
            ),
        ],
    )
    router.reload_catalog_index()
    yield
    router.reload_catalog_index()


@pytest.mark.parametrize(
    ("query", "expected_title"),
    [
        ("Хочу статую Будды", "Статуя Будды Шакьямуни"),
        ("Ищу амулет Будды", "Амулет с Буддой"),
        ("Нужны четки", "Коралловые чётки"),
        ("Есть ваджра?", "Ваджра пятиконечная"),
        ("Покажи тханку", "Тханка Зеленой Тары"),
        ("Нужна поющая чаша", "Поющая чаша"),
    ],
)
def test_product_entity_routing(query, expected_title):
    result = router.route_query(query)
    assert result.intent == "product"
    assert result.matched_title == expected_title


def test_travel_context_wins_over_product_country_match():
    result = router.route_query("Есть поездка в Непал?")
    assert result.intent == "tour"
    assert result.matched_title == "Лапчи — место силы Миларепы"


def test_unknown_tour_place_does_not_return_random_tour():
    result = router.route_query("Поход в Атлантиду")
    assert result.intent == "tour"
    assert result.matched_title is None


def test_wrong_product_entity_does_not_return_another_entity():
    result = router.route_query("Статуя Зеленой Тары")
    assert result.intent == "product"
    assert result.matched_title is None


def test_known_typo_is_corrected():
    result = router.route_query("кайлос")
    assert result.intent == "tour"
    assert result.matched_title == "Тибет + Кайлас — 18 дней"


def test_unknown_store_item_has_no_random_match():
    result = router.route_query("Есть велосипед?")

    assert result.intent == "unknown"
    assert result.matched_title is None
