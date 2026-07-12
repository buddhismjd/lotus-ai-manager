from __future__ import annotations

from backend.sales_assistant.service import SalesAssistant


def main() -> int:
    assistant = SalesAssistant()
    cases = (
        "Какие есть туры в сентябре?",
        "Сколько стоит тур на Кайлас?",
        "Хочу консультацию буддолога-психолога",
        "Как связаться с менеджером?",
    )

    print("=" * 72)
    print("AI BODHI SALES DIALOGUE MANAGER DIAGNOSTICS")
    print("=" * 72)
    for index, query in enumerate(cases, start=1):
        reply = assistant.reply(query, f"diagnostic-{index}")
        print(f"Query: {query}")
        print(f"Topic: {reply.topic}")
        print(f"Kind: {reply.kind}")
        print(f"Next action: {reply.next_action.value}")
        print(f"Suggestions: {len(reply.suggestions)}")
        print(f"Requires manager: {reply.needs_manager}")
        print("-" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
