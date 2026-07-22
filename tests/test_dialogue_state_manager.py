from __future__ import annotations

from backend.sales_assistant.service import SalesAssistant, SalesReply
from backend.sales_assistant.state import DialogueState, DialogueStateStore


def test_state_store_isolated_by_session() -> None:
    store = DialogueStateStore()
    first = store.get("first")
    second = store.get("second")

    first.topic = "tour"
    first.month = 9

    assert second.topic == "unknown"
    assert second.month is None


def test_tour_list_is_remembered_for_follow_up_selection() -> None:
    assistant = SalesAssistant()

    first = assistant.reply("Какие есть туры в сентябре?", "selection")
    second = assistant.reply("Помогите подобрать подходящий тур", "selection")

    assert first.kind == "tour_list"
    assert second.kind == "tour_selection"
    assert "Долина Маркха" in second.answer
    assert "Кайлас" in second.answer
    assert "Выберите путешествие" in second.answer
    assert "треккинг" not in second.answer.casefold()
    assert "сложност" not in second.answer.casefold()
    assert len(second.suggestions) >= 2


def test_follow_up_price_uses_active_tour() -> None:
    assistant = SalesAssistant()

    details = assistant.reply("Расскажите про Кайлас", "price-follow-up")
    price = assistant.reply("А сколько стоит?", "price-follow-up")

    assert details.topic == "tour"
    assert price.kind == "tour_price"
    assert "Кайлас" in price.answer
    assert "не опубликована" in price.answer
    assert price.needs_manager is True


def test_ambiguous_follow_up_after_multiple_tours_asks_which_one() -> None:
    assistant = SalesAssistant()

    assistant.reply("Какие есть туры в сентябре?", "ambiguous")
    reply = assistant.reply("А сколько стоит?", "ambiguous")

    assert reply.kind == "tour_clarification"
    assert "о каком из найденных туров" in reply.answer
    assert "Долина Маркха" in reply.answer
    assert "Кайлас" in reply.answer


def test_reset_removes_dialogue_context() -> None:
    assistant = SalesAssistant()

    assistant.reply("Какие есть туры в сентябре?", "reset-me")
    assistant.reset("reset-me")
    reply = assistant.reply("Помогите подобрать подходящий тур", "reset-me")

    assert reply.kind != "tour_selection"


def test_dialogue_state_snapshot_is_copy() -> None:
    store = DialogueStateStore()
    state = store.get("snapshot")
    state.topic = "tour"
    state.candidate_tour_ids = ("one", "two")

    snapshot = store.snapshot("snapshot")
    snapshot.topic = "product"

    assert store.get("snapshot").topic == "tour"
    assert snapshot.candidate_tour_ids == ("one", "two")


def test_standalone_country_query_uses_country_collection(monkeypatch) -> None:
    from backend.catalog.collection_builder import CollectionItem
    import backend.sales_assistant.service as service_module

    captured: list[str] = []

    def fake_collection(query: str):
        captured.append(query)
        return [
            CollectionItem(
                id="lapchi",
                title="Лапчи — место силы Миларепы",
                url="https://example.com/lapchi",
                material="Непал",
            )
        ]

    monkeypatch.setattr(service_module, "build_tour_collection", fake_collection)
    assistant = SalesAssistant()

    reply = assistant.reply("Непал", "standalone-country")

    assert captured == ["Непал"]
    assert reply.kind == "tour_collection"
    assert len(reply.items) == 1
    assert reply.items[0]["title"] == "Лапчи — место силы Миларепы"


def test_dialogue_wrapper_preserves_collection_items() -> None:
    assistant = SalesAssistant()
    reply = assistant._with_dialogue(
        SalesReply(
            answer="Подборка готова.",
            kind="product_collection",
            topic="product",
            items=({"id": "product-1", "title": "Статуя"},),
        ),
        "product_search",
    )

    assert reply.items == ({"id": "product-1", "title": "Статуя"},)
