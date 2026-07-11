from backend.catalog.product_intelligence import analyze_product


def test_mixed_script_statue_is_detected() -> None:
    # The first character is Latin C, visually similar to Cyrillic С.
    result = analyze_product(
        title="Cтатуя Будды Амитабхи",
        description="Медная статуя для практики.",
    )

    assert result.product_type == "statue"


def test_protective_sticker_is_ritual_item() -> None:
    result = analyze_product(
        title='Защитная наклейка "Калачакра"',
        description="Защитный символ.",
    )

    assert result.product_type == "ritual_item"
    assert "protection" in result.usages


def test_bhutanese_phallus_is_ritual_item() -> None:
    result = analyze_product(
        title="Бутанский пенис",
        description="Традиционный бутанский защитный символ.",
    )

    assert result.product_type == "ritual_item"


def test_regular_statue_still_works() -> None:
    result = analyze_product(
        title="Статуя Белой Тары",
        description="Латунная статуя для домашнего алтаря.",
    )

    assert result.product_type == "statue"
