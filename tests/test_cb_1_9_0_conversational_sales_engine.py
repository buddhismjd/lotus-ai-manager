from backend.catalog.collection_builder import CollectionItem
from backend.sales_assistant.conversation_decision import (
    ConversationDecisionType,
    decide_conversation_action,
)
from backend.sales_assistant.service import SalesAssistant
from backend.sales_assistant.state import DialogueState


def _item() -> CollectionItem:
    return CollectionItem(
        id="gift-1",
        title="Подарочный товар",
        url="https://example.test/gift-1",
        image_url="https://example.test/gift-1.jpg",
        price="5 000 ₽",
        availability="В наличии",
    )


def test_direct_product_selection_does_not_ask_clarification() -> None:
    decision = decide_conversation_action("Покажи тханки Калачакры")

    assert decision.action == ConversationDecisionType.SHOW_RESULTS
    assert decision.question is None


def test_direct_tour_selection_does_not_ask_clarification() -> None:
    decision = decide_conversation_action("Какие туры есть в Непал?")

    assert decision.action == ConversationDecisionType.SHOW_RESULTS


def test_single_clarification_is_saved_in_dialogue_state() -> None:
    assistant = SalesAssistant()
    session_id = "cb-1-9-single-clarification"

    reply = assistant.reply("Хочу подарок", session_id=session_id)
    state = assistant._states.get(session_id)

    assert reply.kind == "commercial_clarification"
    assert "практики" in reply.answer
    assert state.pending_clarification_query == "Хочу подарок"
    assert state.pending_clarification_type == "gift_purpose"


def test_no_double_clarification_after_user_answer(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.sales_assistant.service.build_product_collection",
        lambda query, *args, **kwargs: [_item()],
    )
    assistant = SalesAssistant()
    session_id = "cb-1-9-no-double"

    first = assistant.reply("Хочу подарок", session_id=session_id)
    second = assistant.reply("Для буддийской практики", session_id=session_id)

    assert first.kind == "commercial_clarification"
    assert second.kind == "product_collection"
    assert second.items
    state = assistant._states.get(session_id)
    assert state.pending_clarification_query is None


def test_immediate_card_rendering_for_specific_product(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.sales_assistant.service.build_product_collection",
        lambda query, *args, **kwargs: [_item()],
    )
    assistant = SalesAssistant()

    reply = assistant.reply(
        "Покажи товары с Калачакрой",
        session_id="cb-1-9-immediate-card",
    )

    assert reply.kind == "product_collection"
    assert reply.items[0]["title"] == "Подарочный товар"
    assert reply.items[0]["button_label"] == "Открыть товар"


def test_state_clarification_round_trip() -> None:
    state = DialogueState()
    state.start_commercial_clarification(query="Хочу что-нибудь домой", clarification_type="home_purpose")

    restored = DialogueState.from_dict(state.to_dict())
    combined = restored.consume_commercial_clarification("Для домашнего алтаря")

    assert combined == "Хочу что-нибудь домой. Для домашнего алтаря"
    assert restored.pending_clarification_query is None
