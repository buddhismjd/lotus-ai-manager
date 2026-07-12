from backend.knowledge_graph.contract import (
    AspectType,
    KnowledgeAspect,
    KnowledgeGraphContract,
)
from backend.knowledge_graph.models import KnowledgeRelation, RelationType
from backend.knowledge_graph.repository import KnowledgeGraphRepository


def _repository() -> KnowledgeGraphRepository:
    repository = KnowledgeGraphRepository()
    repository.add_entity(
        KnowledgeAspect(
            entity_id="white_tara",
            entity_type=AspectType.BODHISATTVA,
            name="Белая Тара",
            aliases=("Ситатара",),
        )
    )
    repository.add_entity(
        KnowledgeAspect(
            entity_id="product:1",
            entity_type=AspectType.PRODUCT,
            name="Статуя Белой Тары",
        )
    )
    repository.add_relation(
        KnowledgeRelation(
            source_id="white_tara",
            relation_type=RelationType.REPRESENTED_BY,
            target_id="product:1",
        )
    )
    return repository


def test_repository_implements_graph_contract() -> None:
    repository = _repository()
    assert isinstance(repository, KnowledgeGraphContract)


def test_contract_uses_aspect_terminology_without_data_duplication() -> None:
    repository = _repository()
    aspect = repository.get_aspect("white_tara")

    assert aspect is repository.get_entity("white_tara")
    assert aspect is not None
    assert aspect.entity_type is AspectType.BODHISATTVA


def test_contract_filters_aspects_by_type_and_alias() -> None:
    repository = _repository()

    assert repository.list_aspects(AspectType.PRODUCT)[0].entity_id == "product:1"
    assert repository.find_aspects("Ситатара")[0].entity_id == "white_tara"


def test_contract_builds_typed_neighborhood() -> None:
    repository = _repository()
    neighborhood = repository.neighborhood("white_tara")

    assert neighborhood is not None
    assert neighborhood.aspect.entity_id == "white_tara"
    assert neighborhood.outgoing[0].relation_type is RelationType.REPRESENTED_BY
    assert [item.entity_id for item in neighborhood.neighbors] == ["product:1"]


def test_unknown_aspect_has_no_neighborhood() -> None:
    assert _repository().neighborhood("unknown") is None
