from backend.knowledge_graph.models import (
    EntityType,
    KnowledgeEntity,
    KnowledgeRelation,
    RelationType,
)


def test_taras_are_bodhisattvas() -> None:
    white = KnowledgeEntity(
        entity_id="white_tara",
        entity_type=EntityType.BODHISATTVA,
        name="Белая Тара",
    )
    green = KnowledgeEntity(
        entity_id="green_tara",
        entity_type=EntityType.BODHISATTVA,
        name="Зелёная Тара",
    )

    assert white.entity_type is EntityType.BODHISATTVA
    assert green.entity_type is EntityType.BODHISATTVA


def test_vajra_and_phurba_are_practice_items() -> None:
    for entity_id, name in (
        ("vajra", "Ваджра"),
        ("phurba", "Пхурба"),
    ):
        entity = KnowledgeEntity(
            entity_id=entity_id,
            entity_type=EntityType.PRACTICE_ITEM,
            name=name,
        )
        assert entity.entity_type is EntityType.PRACTICE_ITEM
