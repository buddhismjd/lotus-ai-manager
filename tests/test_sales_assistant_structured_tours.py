from __future__ import annotations

from backend.sales_assistant.service import SalesAssistant


def test_live_catalog_returns_multiple_september_tours() -> None:
    reply = SalesAssistant().reply("Какие есть туры в сентябре?", "structured-september")
    assert reply.kind == "tour_list"
    assert "Долина Маркха" in reply.answer
    assert "Тибет + Кайлас" in reply.answer
    assert "не нашёл опубликованных туров" not in reply.answer
