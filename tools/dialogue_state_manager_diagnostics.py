from __future__ import annotations

from backend.sales_assistant.service import SalesAssistant


def main() -> None:
    assistant = SalesAssistant()
    session = "diagnostics"
    first = assistant.reply("Какие есть туры в сентябре?", session)
    second = assistant.reply("Помогите подобрать подходящий тур", session)
    third = assistant.reply("Расскажите про Кайлас", session)
    fourth = assistant.reply("А сколько стоит?", session)

    print("=" * 72)
    print("AI BODHI DIALOGUE STATE MANAGER DIAGNOSTICS")
    print("=" * 72)
    print(f"Tour list: {first.kind}")
    print(f"Selection follow-up: {second.kind}")
    print(f"Active tour: {third.title or '-'}")
    print(f"Price follow-up: {fourth.kind}")
    print(f"Price manager handoff: {fourth.needs_manager}")

    assert first.kind == "tour_list"
    assert second.kind == "tour_selection"
    assert third.topic == "tour"
    assert fourth.kind == "tour_price"
    assert fourth.needs_manager is True


if __name__ == "__main__":
    main()
