from fastapi.testclient import TestClient

import backend.main as main_module
from backend.services.response_builder import BuiltResponse


client = TestClient(main_module.app)


def test_bodhi_chat_rejects_empty_message() -> None:
    response = client.post("/api/bodhi/chat", json={"message": "   "})

    assert response.status_code == 200
    assert response.json()["status"] == "empty"


def test_bodhi_chat_returns_user_facing_answer(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "answer_query",
        lambda _: BuiltResponse(
            kind="tour",
            text="🌸 Подходящее путешествие.",
            title="Кайлас",
            url="https://example.com/kailash",
        ),
    )

    response = client.post(
        "/api/bodhi/chat",
        json={"message": "Хочу на Кайлас"},
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "bodhi_tour"
    assert payload["answer"] == "🌸 Подходящее путешествие."
    assert payload["title"] == "Кайлас"
    assert payload["url"] == "https://example.com/kailash"


def test_country_query_has_priority_over_generic_route(monkeypatch) -> None:
    from types import SimpleNamespace
    from backend.catalog.collection_builder import CollectionItem

    monkeypatch.setattr(
        main_module,
        "answer_query",
        lambda _: BuiltResponse(kind="fallback", text="fallback"),
    )
    monkeypatch.setattr(
        main_module,
        "route_query",
        lambda _: SimpleNamespace(intent="product"),
    )
    monkeypatch.setattr(
        main_module,
        "build_tour_collection",
        lambda _: [
            CollectionItem(
                id="nepal-1",
                title="Непал: Муктинатх",
                url="https://example.test/nepal-1",
                image_url="https://example.test/nepal-1.jpg",
                item_type="tour",
            ),
            CollectionItem(
                id="nepal-2",
                title="Непал: Лапчи",
                url="https://example.test/nepal-2",
                image_url="https://example.test/nepal-2.jpg",
                item_type="tour",
            ),
        ],
    )

    response = client.post("/api/bodhi/chat", json={"message": "Непал"})
    payload = response.json()

    assert payload["kind"] == "tour_collection"
    assert [item["title"] for item in payload["items"]] == [
        "Непал: Муктинатх",
        "Непал: Лапчи",
    ]
    assert all(item["image_url"] for item in payload["items"])
