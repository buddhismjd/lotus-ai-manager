from backend.knowledge_graph.loader import load_graph
from backend.semantic_engine.engine import answer_semantic_query
from backend.semantic_engine.models import SemanticIntent


def test_semantic_engine_describes_milarepa() -> None:
    answer = answer_semantic_query(
        "Расскажи про Миларепу",
        repository=load_graph(),
    )

    assert answer.matched is True
    assert answer.entity_id == "milarepa"
    assert "Миларепа" in answer.text
    assert "Лапчи" in answer.text
    assert "Кагью" in answer.text


def test_semantic_engine_finds_practices() -> None:
    answer = answer_semantic_query(
        "Какие практики связаны с Миларепой?",
        repository=load_graph(),
    )

    assert answer.matched is True
    assert answer.intent is SemanticIntent.FIND_PRACTICES
    assert "Медитация" in answer.text


def test_semantic_engine_handles_missing_products() -> None:
    answer = answer_semantic_query(
        "Какие товары есть по Белой Таре?",
        repository=load_graph(),
    )

    assert answer.matched is True
    assert "пока нет связанных объектов" in answer.text
