from types import SimpleNamespace

from backend.tours.intelligence import build_tour_profile


def tour(title: str, description: str, url: str):
    return SimpleNamespace(
        title=title,
        description=description,
        url=url,
        country="",
        region="",
        difficulty="",
        guide="",
        keywords=[],
        source_id="",
        id="",
    )


def test_lapchi_profile() -> None:
    profile = build_tour_profile(
        tour(
            "Лапчи — место силы Миларепы",
            (
                "8-дневный паломнический поход в Непале. "
                "Маршрут Катманду — Лапчи. "
                "Максимальная высота 3780 м. "
                "Медитация и посещение пещер Миларепы."
            ),
            "https://example.com/lapchi",
        )
    )

    assert "Непал" in profile.countries
    assert "Лапчи" in profile.destinations
    assert "Миларепа" in profile.aspects
    assert "поход" in profile.practices
    assert "медитация" in profile.practices
    assert profile.duration_days == 8
    assert profile.max_altitude_m == 3780


def test_kailash_profile() -> None:
    profile = build_tour_profile(
        tour(
            "Тибет + Кайлас — 18 дней",
            "Паломничество и кора вокруг Кайласа.",
            "https://example.com/kailash",
        )
    )

    assert "Тибет" in profile.countries
    assert "Кайлас" in profile.destinations
    assert "кора" in profile.practices
    assert profile.duration_days == 18


def test_hyphenated_duration_forms() -> None:
    for title in (
        "Лапчи — 8-дневный поход",
        "Лапчи — 8 дневный поход",
        "Лапчи — 8 дней",
    ):
        profile = build_tour_profile(
            tour(
                title,
                "Паломническая программа в Непале.",
                "https://example.com/lapchi-8-days",
            )
        )
        assert profile.duration_days == 8


def test_india_ladakh_and_zanskar_are_detected() -> None:
    profile = build_tour_profile(
        tour(
            "Ладакх, королевство Занскар",
            "Путешествие по северу Индии.",
            "https://example.com/tur-v-ladakh-zanskar",
        )
    )

    assert "Индия" in profile.countries
    assert "Ладакх" in profile.regions
    assert "Занскар" in profile.regions


def test_altai_and_belukha_are_in_russia() -> None:
    profile = build_tour_profile(
        tour(
            "Поход к подножию горы Белуха",
            "Маршрут проходит по Алтаю.",
            "https://example.com/altay-beluha",
        )
    )

    assert "Россия" in profile.countries
    assert "Алтай" in profile.regions
    assert "Белуха" in profile.regions


def test_kullu_and_markha_are_in_india() -> None:
    kullu = build_tour_profile(
        tour(
            "По стопам Рериха — Долина Куллу",
            "",
            "https://example.com/india-tur-dolina-kullu",
        )
    )
    markha = build_tour_profile(
        tour(
            "Долина Маркха и Канг Ятсе 2",
            "",
            "https://example.com/trek-markha-kang-yatse",
        )
    )

    assert "Индия" in kullu.countries
    assert "Долина Куллу" in kullu.regions
    assert "Индия" in markha.countries
    assert "Долина Маркха" in markha.regions
