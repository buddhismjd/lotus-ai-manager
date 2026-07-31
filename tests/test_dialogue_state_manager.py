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
    assert "1450" in price.answer
    assert "USD" in price.answer
    assert price.needs_manager is False


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


def test_new_country_query_resets_previous_tour_context(monkeypatch) -> None:
    from backend.catalog.collection_builder import CollectionItem
    import backend.sales_assistant.service as service_module

    captured: list[str] = []

    def fake_collection(query: str):
        captured.append(query)
        if "инд" in query.casefold():
            return [
                CollectionItem(
                    id="india-tour",
                    title="Индия — Ладакх",
                    url="https://example.com/india",
                    material="Индия",
                )
            ]
        return [
            CollectionItem(
                id="nepal-tour",
                title="Непал — Муктинатх",
                url="https://example.com/nepal",
                material="Непал",
            )
        ]

    monkeypatch.setattr(service_module, "build_tour_collection", fake_collection)
    assistant = SalesAssistant()

    assistant.reply("Какие туры в Непал?", "country-switch")
    state = assistant._states.get("country-switch")
    state.active_tour_id = "nepal-tour"
    state.active_title = "Непал — Муктинатх"
    state.active_url = "https://example.com/nepal"

    reply = assistant.reply("Что по Индии?", "country-switch")

    assert captured[-1] == "Что по Индии?"
    assert reply.kind == "tour_collection"
    assert len(reply.items) == 1
    assert reply.items[0]["title"] == "Индия — Ладакх"
    state = assistant._states.get("country-switch")
    assert state.active_tour_id is None
    assert state.active_title is None


def test_active_product_collection_supports_numbered_follow_up(monkeypatch) -> None:
    from backend.catalog.collection_builder import CollectionItem
    import backend.sales_assistant.service as service_module

    products = [
        CollectionItem(id="p1", title="Статуя Белой Тары", url="https://example.com/p1", image_url="https://example.com/p1.jpg"),
        CollectionItem(id="p2", title="Статуя Зелёной Тары", url="https://example.com/p2", image_url="https://example.com/p2.jpg"),
        CollectionItem(id="p3", title="Статуя Манджушри", url="https://example.com/p3", image_url="https://example.com/p3.jpg"),
    ]
    monkeypatch.setattr(service_module, "build_product_collection", lambda *args, **kwargs: products)
    assistant = SalesAssistant()

    state = assistant._states.get("active-products")
    from backend.catalog.commercial_cards import commercial_cards
    state.topic = "product"
    state.remember_collection(topic="product", items=commercial_cards(products))
    first = SalesReply(answer="Подборка", kind="product_collection", topic="product", items=state.active_collection_items)
    second = assistant.reply("Покажи второй", "active-products")

    assert len(first.items) == 3
    assert second.kind == "product_item"
    assert len(second.items) == 1
    assert second.items[0]["id"] == "p2"
    assert second.items[0]["image_url"] == "https://example.com/p2.jpg"
    assert second.title == "Статуя Зелёной Тары"


def test_active_collection_can_repeat_all_items(monkeypatch) -> None:
    from backend.catalog.collection_builder import CollectionItem
    import backend.sales_assistant.service as service_module

    products = [
        CollectionItem(id="p1", title="Ваджра", url="https://example.com/p1"),
        CollectionItem(id="p2", title="Пхурба", url="https://example.com/p2"),
    ]
    monkeypatch.setattr(service_module, "build_product_collection", lambda *args, **kwargs: products)
    assistant = SalesAssistant()

    state = assistant._states.get("active-more")
    from backend.catalog.commercial_cards import commercial_cards
    state.topic = "product"
    state.remember_collection(topic="product", items=commercial_cards(products))
    reply = assistant.reply("Есть ещё?", "active-more")

    assert reply.kind == "product_collection"
    assert [item["id"] for item in reply.items] == ["p1", "p2"]
    assert "2 вариантов" in reply.answer


def test_active_collection_survives_state_serialization() -> None:
    state = DialogueState()
    state.remember_collection(
        topic="product",
        items=({"id": "p1", "title": "Ваджра", "url": "https://example.com/p1"},),
    )

    restored = DialogueState.from_dict(state.to_dict())

    assert restored.active_collection_topic == "product"
    assert restored.active_collection_items == (
        {"id": "p1", "title": "Ваджра", "url": "https://example.com/p1"},
    )
