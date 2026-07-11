from backend.catalog.text_normalization import (
    normalize_search_text,
    normalized_contains,
)
from backend.catalog.product_intelligence import analyze_product


def test_mixed_script_title_is_normalized() -> None:
    assert normalize_search_text(
        "Cтатуя Будды Амитабхи"
    ) == normalize_search_text(
        "Статуя Будды Амитабхи"
    )


def test_expected_fragment_matches_mixed_script_title() -> None:
    assert normalized_contains(
        "Стату",
        "Cтатуя Будды Амитабхи",
    )


def test_white_tara_is_entity_without_forced_product_type() -> None:
    intelligence = analyze_product(
        title="Белая Тара",
    )

    assert intelligence.product_type is None
    assert "Белая Тара" in intelligence.entities
