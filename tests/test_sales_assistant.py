from backend.services.response_builder import BuiltResponse
import backend.sales_assistant.service as service_module
from backend.sales_assistant.service import SalesAssistant


def test_psychologist_answer_is_factual() -> None:
    reply = SalesAssistant().reply("Чем помогает буддолог-психолог?", "a")
    assert reply.topic == "psychologist"
    assert "стресс" in reply.answer
    assert not reply.needs_manager


def test_unknown_psychologist_price_is_not_invented() -> None:
    assistant = SalesAssistant()
    assistant.reply("Хочу консультацию буддолога", "a")
    reply = assistant.reply("Сколько стоит?", "a")
    assert reply.topic == "psychologist"
    assert "не указана" in reply.answer
    assert reply.needs_manager


def test_existing_bodhi_response_is_reused(monkeypatch) -> None:
    monkeypatch.setattr(service_module, "route_query", lambda _: type("R", (), {"intent": "tour"})())
    monkeypatch.setattr(service_module, "answer_query", lambda _: BuiltResponse(kind="tour", text="Тур найден", title="Кайлас", url="https://example.com"))
    reply = SalesAssistant().reply("Есть тур на Кайлас?", "a")
    assert reply.kind == "tour"
    assert reply.title == "Кайлас"


def test_sessions_do_not_share_context(monkeypatch) -> None:
    assistant = SalesAssistant()
    assistant.reply("Хочу консультацию", "one")
    monkeypatch.setattr(service_module, "route_query", lambda _: type("R", (), {"intent": "unknown"})())
    monkeypatch.setattr(service_module, "answer_query", lambda _: BuiltResponse(kind="fallback", text="Нет данных"))
    reply = assistant.reply("Сколько стоит?", "two")
    assert reply.topic == "unknown"
