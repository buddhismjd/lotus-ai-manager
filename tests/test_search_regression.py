from types import SimpleNamespace

import pytest

import backend.rag.dynamic_query_router as router


def product(
    title: str,
    category: str,
    description: str,
    url: str,
):
    return SimpleNamespace(
        title=title,
        category=category,
        description=description,
        material="",
        keywords=[],
        url=url,
    )


def tour(
    title: str,
    country: str,
    region: str,
    description: str,
    url: str,
):
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
    products = [
        product(
            "Статуя Будды Шакьямуни",
            "Статуи",
            "Буддийская статуя для домашнего алтаря",
            "https://example.com/statue-buddha",
        ),
        product(
            "Амулет с Буддой",
            "Подвески",
            "Амулет с изображением Будды",
            "https://example.com/amulet-buddha",
        ),
        product(
            "Чётки из сандалового дерева",
            "Чётки",
            "Мала для ежедневной практики",
            "https://example.com/mala",
        ),
        product(
            "Ваджра пятиконечная",
            "Ритуальные предметы",
            "Традиционная ваджра для практики",
            "https://example.com/vajra",
        ),
        product(
            "Тханка Зеленой Тары",
            "Тханки",
            "Буддийское изображение Зеленой Тары",
            "https://example.com/thangka",
        ),
        product(
            "Поющая чаша",
            "Поющие чаши",
            "Чаша для медитации",
            "https://example.com/bowl",
        ),
    ]

    tours = [
        tour(
            "Тибет + Кайлас — 18 дней",
            "Китай",
            "Тибет",
            "Паломническое путешествие к Кайласу",
            "https://example.com/kailash",
        ),
        tour(
            "Лапчи — место силы Миларепы",
            "Непал",
            "Лапчи",
            "Паломнический поход в Лапчи",
            "https://example.com/lapchi",
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
        lambda self: tours,
    )

    router.reload_catalog_index()
    yield
    router.reload_catalog_index()


@pytest.mark.parametrize(
    ("query", "expected_title"),
    [
        ("Хочу статую Будды", "Статуя Будды Шакьямуни"),
        ("Ищу амулет Будды", "Амулет с Буддой"),
        ("Нужны четки", "Чётки из сандалового дерева"),
        ("Есть ваджра?", "Ваджра пятиконечная"),
        ("Покажи тханку", "Тханка Зеленой Тары"),
        ("Нужна поющая чаша", "Поющая чаша"),
    ],
)
def test_product_types(query, expected_title):
    result = router.route_query(query)

    assert result.intent == "product"
    assert result.matched_title == expected_title


@pytest.mark.parametrize(
    ("query", "expected_title"),
    [
        ("Хочу на Кайлас", "Тибет + Кайлас — 18 дней"),
        ("Поход в Лапчи", "Лапчи — место силы Миларепы"),
    ],
)
def test_tours(query, expected_title):
    result = router.route_query(query)

    assert result.intent == "tour"
    assert result.matched_title == expected_title


def test_unknown_product_is_not_random_match():
    result = router.route_query("Есть велосипед?")

    assert result.matched_title is None


@pytest.mark.parametrize(
    ("query", "expected_kind"),
    [
        ("статуя Будды", "statue"),
        ("статую Будды", "statue"),
        ("статуи Будды", "statue"),
        ("амулет Будды", "amulet"),
        ("четки", "mala"),
        ("чётки", "mala"),
        ("ваджру", "vajra"),
        ("тханку", "thangka"),
    ],
)
def test_product_kind_inflections(query, expected_kind):
    assert router.detect_product_kind(query) == expected_kind
