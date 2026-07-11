from backend.knowledge_graph.loader import load_graph
from backend.knowledge_graph.models import (
    EntityType,
    RelationType,
)
from backend.knowledge_graph.validator import (
    has_errors,
    validate_graph,
)


def test_default_graph_loads() -> None:
    repository = load_graph()

    assert repository.get_entity("white_tara") is not None
    assert repository.get_entity("milarepa") is not None
    assert repository.get_entity("lapchi") is not None


def test_graph_types_and_relations() -> None:
    repository = load_graph()

    assert (
        repository.get_entity("white_tara").entity_type
        is EntityType.BODHISATTVA
    )
    assert (
        repository.get_entity("vajra").entity_type
        is EntityType.PRACTICE_ITEM
    )

    relations = repository.outgoing(
        "milarepa",
        RelationType.PRACTICED_AT,
    )

    assert len(relations) == 1
    assert relations[0].target_id == "lapchi"


def test_graph_has_no_validation_errors() -> None:
    repository = load_graph()
    issues = validate_graph(repository)

    assert has_errors(issues) is False
