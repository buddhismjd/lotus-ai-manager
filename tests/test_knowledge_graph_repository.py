import pytest

from backend.knowledge_graph.models import (
    EntityType,
    KnowledgeEntity,
    KnowledgeRelation,
    RelationType,
)
from backend.knowledge_graph.repository import (
    KnowledgeGraphRepository,
)


def test_repository_rejects_conflicting_entity_id() -> None:
    repository = KnowledgeGraphRepository()
    repository.add_entity(
        KnowledgeEntity(
            entity_id="white_tara",
            entity_type=EntityType.BODHISATTVA,
            name="Белая Тара",
        )
    )

    with pytest.raises(ValueError):
        repository.add_entity(
            KnowledgeEntity(
                entity_id="white_tara",
                entity_type=EntityType.BUDDHA,
                name="Другое имя",
            )
        )


def test_neighbors() -> None:
    repository = KnowledgeGraphRepository()

    for entity in (
        KnowledgeEntity(
            entity_id="milarepa",
            entity_type=EntityType.TEACHER,
            name="Миларепа",
        ),
        KnowledgeEntity(
            entity_id="lapchi",
            entity_type=EntityType.PLACE,
            name="Лапчи",
        ),
    ):
        repository.add_entity(entity)

    repository.add_relation(
        KnowledgeRelation(
            source_id="milarepa",
            relation_type=RelationType.PRACTICED_AT,
            target_id="lapchi",
        )
    )

    assert [item.entity_id for item in repository.neighbors("milarepa")] == [
        "lapchi"
    ]
