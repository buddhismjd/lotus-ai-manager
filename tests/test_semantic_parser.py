from backend.knowledge_graph.loader import load_graph
from backend.semantic_engine.models import SemanticIntent
from backend.semantic_engine.parser import parse_semantic_query


def test_describe_entity_query() -> None:
    result = parse_semantic_query(
        "Расскажи про Миларепу",
        repository=load_graph(),
    )

    assert result.entity_id == "milarepa"
    assert result.intent is SemanticIntent.DESCRIBE_ENTITY


def test_find_tours_query() -> None:
    result = parse_semantic_query(
        "Куда можно поехать к Миларепе?",
        repository=load_graph(),
    )

    assert result.entity_id == "milarepa"
    assert result.intent is SemanticIntent.FIND_TOURS


def test_unknown_entity_query() -> None:
    result = parse_semantic_query(
        "Расскажи про несуществующий объект",
        repository=load_graph(),
    )

    assert result.intent is SemanticIntent.UNKNOWN
