from backend.knowledge_graph.models import (
    EntityType,
    KnowledgeEntity,
    KnowledgeRelation,
    RelationType,
)
from backend.knowledge_graph.repository import (
    KnowledgeGraphRepository,
)


def test_relation_with_dict_metadata_can_be_added() -> None:
    repository = KnowledgeGraphRepository()
    repository.add_entity(
        KnowledgeEntity(
            entity_id="milarepa",
            entity_type=EntityType.TEACHER,
            name="Миларепа",
        )
    )
    repository.add_entity(
        KnowledgeEntity(
            entity_id="lapchi",
            entity_type=EntityType.PLACE,
            name="Лапчи",
        )
    )

    relation = KnowledgeRelation(
        source_id="milarepa",
        relation_type=RelationType.PRACTICED_AT,
        target_id="lapchi",
        metadata={"source": "test"},
    )

    repository.add_relation(relation)
    repository.add_relation(relation)

    assert repository.list_relations() == (relation,)


def test_neighbors_work_after_relation_storage_fix() -> None:
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

    assert [
        entity.entity_id
        for entity in repository.neighbors("milarepa")
    ] == ["lapchi"]
