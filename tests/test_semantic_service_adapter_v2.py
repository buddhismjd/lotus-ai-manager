import backend.services.semantic_service_adapter as adapter
from backend.semantic_engine.models import (
    SemanticAnswer,
    SemanticIntent,
)


def test_commercial_product_query_is_rejected() -> None:
    assert (
        adapter.should_use_semantic_fallback(
            "У вас есть Ваджра?"
        )
        is False
    )
    assert (
        adapter.should_use_semantic_fallback(
            "Статуя Белой Тары"
        )
        is False
    )


def test_commercial_tour_query_is_rejected() -> None:
    assert (
        adapter.should_use_semantic_fallback(
            "Поход в Лапчи"
        )
        is False
    )
    assert (
        adapter.should_use_semantic_fallback(
            "Есть поездка в Непал?"
        )
        is False
    )


def test_knowledge_query_is_allowed() -> None:
    assert (
        adapter.should_use_semantic_fallback(
            "Какие практики связаны с Миларепой?"
        )
        is True
    )
    assert (
        adapter.should_use_semantic_fallback(
            "Расскажи про Ваджру"
        )
        is True
    )


def test_rejected_query_does_not_call_engine(monkeypatch) -> None:
    called = False

    def fake_engine(query):
        nonlocal called
        called = True
        return SemanticAnswer(
            matched=True,
            text="wrong",
            intent=SemanticIntent.DESCRIBE_ENTITY,
            entity_id="vajra",
            confidence=0.95,
        )

    monkeypatch.setattr(
        adapter,
        "answer_semantic_query",
        fake_engine,
    )

    assert adapter.semantic_built_response(
        "У вас есть Ваджра?"
    ) is None
    assert called is False


def test_allowed_query_is_converted(monkeypatch) -> None:
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
