import backend.services.semantic_service_adapter as adapter
from backend.semantic_engine.models import (
    SemanticAnswer,
    SemanticIntent,
)


def test_semantic_knowledge_answer_is_converted(monkeypatch) -> None:
    monkeypatch.setattr(
        adapter,
        "answer_semantic_query",
        lambda query: SemanticAnswer(
            matched=True,
            text="Ваджра — предмет для практики.",
            intent=SemanticIntent.DESCRIBE_ENTITY,
            entity_id="vajra",
            confidence=0.95,
        ),
    )

    response = adapter.semantic_built_response(
        "Расскажи про Ваджру"
    )

    assert response is not None
    assert response.kind == "product"
    assert "предмет для практики" in response.text


def test_semantic_practice_answer_is_converted(monkeypatch) -> None:
    monkeypatch.setattr(
        adapter,
        "answer_semantic_query",
        lambda query: SemanticAnswer(
            matched=True,
            text="Практика: Медитация",
            intent=SemanticIntent.FIND_PRACTICES,
            entity_id="milarepa",
            confidence=0.95,
        ),
    )

    response = adapter.semantic_built_response(
        "Какие практики связаны с Миларепой?"
    )

    assert response is not None
    assert "Медитация" in response.text


def test_commercial_product_query_is_not_intercepted(monkeypatch) -> None:
    called = False

    def fake_engine(query):
        nonlocal called
        called = True
        return SemanticAnswer(
            matched=True,
            text="wrong",
            intent=SemanticIntent.FIND_PRODUCTS,
            entity_id="white_tara",
            confidence=0.95,
        )

    monkeypatch.setattr(
        adapter,
        "answer_semantic_query",
        fake_engine,
    )

    response = adapter.semantic_built_response(
        "Какие товары есть по Белой Таре?"
    )

    assert response is None
    assert called is False


def test_commercial_tour_query_is_not_intercepted(monkeypatch) -> None:
    called = False

    def fake_engine(query):
        nonlocal called
        called = True
        return SemanticAnswer(
            matched=True,
            text="wrong",
            intent=SemanticIntent.FIND_TOURS,
            entity_id="milarepa",
            confidence=0.95,
        )

    monkeypatch.setattr(
        adapter,
        "answer_semantic_query",
        fake_engine,
    )

    response = adapter.semantic_built_response(
        "Куда можно поехать к Миларепе?"
    )

    assert response is None
    assert called is False


def test_unmatched_semantic_answer_returns_none(monkeypatch) -> None:
    monkeypatch.setattr(
        adapter,
        "answer_semantic_query",
        lambda query: SemanticAnswer(
            matched=False,
            text="",
            intent=SemanticIntent.UNKNOWN,
            confidence=0.0,
        ),
    )

    assert (
        adapter.semantic_built_response(
            "Расскажи про неизвестный объект"
        )
        is None
    )
