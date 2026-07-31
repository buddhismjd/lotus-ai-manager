from dataclasses import dataclass

import pytest

from backend.decision import DecisionContext, DecisionEngine, DecisionResult, NextAction


def test_empty_engine_preserves_existing_response() -> None:
    context = DecisionContext(
        user_message="Непал",
        intent="tour",
        current_reply="Я нашёл туры в Непал.",
        cards=({"type": "tour", "title": "Лапчи"},),
    )

    result = DecisionEngine().decide(context)

    assert result.reply_text == context.current_reply
    assert result.cards[0]["title"] == "Лапчи"
    assert result.next_action is NextAction.RESPOND
    assert result.policy == "passthrough"


def test_context_converts_mutable_collections_to_read_only_values() -> None:
    state = {"country": "Непал"}
    card = {"title": "Лапчи"}
    context = DecisionContext("Непал", cards=(card,), conversation_state=state)
    state["country"] = "Индия"
    card["title"] = "Изменено"

    assert context.conversation_state["country"] == "Непал"
    assert context.cards[0]["title"] == "Лапчи"
    with pytest.raises(TypeError):
        context.conversation_state["country"] = "Тибет"  # type: ignore[index]


def test_result_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="confidence"):
        DecisionResult(reply_text="", confidence=1.1)


@dataclass(frozen=True)
class _Policy:
    name: str
    priority: int
    result: DecisionResult | None

    def decide(self, context: DecisionContext) -> DecisionResult | None:
        return self.result


def test_engine_uses_highest_priority_applicable_policy() -> None:
    low = _Policy("low", 10, DecisionResult("low", policy="low"))
    high = _Policy("high", 100, DecisionResult("high", policy="high"))

    result = DecisionEngine((low, high)).decide(DecisionContext("test"))

    assert result.reply_text == "high"
    assert result.policy == "high"


def test_engine_continues_when_policy_defers() -> None:
    first = _Policy("first", 100, None)
    second = _Policy("second", 10, DecisionResult("handled", policy="second"))

    result = DecisionEngine((first, second)).decide(DecisionContext("test"))

    assert result.reply_text == "handled"


def test_engine_rejects_duplicate_policy_names() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        DecisionEngine((_Policy("same", 10, None), _Policy("same", 20, None)))


def test_engine_has_no_dependency_on_sales_or_widget_packages() -> None:
    import backend.decision.engine as engine_module
    import backend.decision.models as models_module

    source = engine_module.__loader__.get_source(engine_module.__name__)  # type: ignore[union-attr]
    source += models_module.__loader__.get_source(models_module.__name__)  # type: ignore[union-attr]

    assert "backend.sales_assistant" not in source
    assert "backend.widget" not in source
