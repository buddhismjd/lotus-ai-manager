from backend.sales_assistant.service import SalesAssistant


def main() -> None:
    reply = SalesAssistant().reply("На Кайлас возите?", "formatter-smoke")
    assert reply.topic == "tour"
    assert "План маршрута" not in reply.answer
    assert "Путешествия\nМагазин" not in reply.answer
    assert "Подробнее о туре" in reply.answer
    print("SMOKE PASSED")
    print(reply.answer)


if __name__ == "__main__":
    main()
