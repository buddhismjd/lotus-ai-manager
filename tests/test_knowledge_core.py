from backend.knowledge.knowledge_advisor import (
    advise_product_description,
)
from backend.knowledge.knowledge_core import (
    get_knowledge_definition,
    list_by_kind,
    load_knowledge_core,
)


def test_taras_are_bodhisattvas() -> None:
    white = get_knowledge_definition("white_tara")
    green = get_knowledge_definition("green_tara")

    assert white is not None
    assert green is not None
    assert white.kind == "bodhisattva"
    assert green.kind == "bodhisattva"
    assert white.kind_label == "Бодхисаттва"


def test_vajra_and_phurba_are_practice_items() -> None:
    vajra = get_knowledge_definition("vajra")
    phurba = get_knowledge_definition("phurba")

    assert vajra is not None
    assert phurba is not None
    assert vajra.kind == "practice_item"
    assert phurba.kind == "practice_item"
    assert vajra.kind_label == "Предмет для практики"


def test_relations_are_valid() -> None:
    core = load_knowledge_core()

    assert "green_tara" in core["white_tara"].related_knowledge_ids
    assert "white_tara" in core["green_tara"].related_knowledge_ids
    assert "phurba" in core["vajra"].related_knowledge_ids


def test_description_advisor_for_vajra() -> None:
    result = advise_product_description(
        "vajra",
        existing_description="Ритуальный предмет.",
    )

    assert result is not None
    assert "количество концов" in result.missing_fields
    assert "материал" in result.missing_fields
    assert "размер" in result.missing_fields
