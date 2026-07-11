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
