from __future__ import annotations

from backend.sales_assistant.service import SalesAssistant


def main() -> None:
    assistant = SalesAssistant()
    session = "smoke"
    assistant.reply("Какие есть туры в сентябре?", session)
    reply = assistant.reply("Помогите подобрать подходящий тур", session)

    assert reply.kind == "tour_selection"
    assert "Кайлас" in reply.answer
    assert "Долина Маркха" in reply.answer
    print("SMOKE PASSED")
    print(f"Kind: {reply.kind}")
    print(f"Suggestions: {len(reply.suggestions)}")


if __name__ == "__main__":
    main()
