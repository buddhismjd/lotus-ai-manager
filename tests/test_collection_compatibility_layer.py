from __future__ import annotations

import backend.sales_assistant.service as service_module
from backend.sales_assistant.service import SalesAssistant
from backend.services.response_builder import BuiltResponse


def test_exact_tour_query_reuses_bodhi_response(monkeypatch) -> None:
    route = type("Route", (), {"intent": "tour"})()
    monkeypatch.setattr(service_module, "route_query", lambda _: route)
    monkeypatch.setattr(
        service_module,
        "answer_query",
        lambda _: BuiltResponse(
            kind="tour",
            text="Тур найден",
            title="Кайлас",
            url="https://example.test/kailash",
        ),
    )

    reply = SalesAssistant().reply("Есть тур на Кайлас?", "exact-tour")

    assert reply.kind == "tour"
    assert reply.title == "Кайлас"


def test_missing_price_keeps_honest_compatibility_wording() -> None:
    text = service_module.warm_missing_price("Кайлас")

    assert "не буду придумывать" in text
    assert "не указана" in text
