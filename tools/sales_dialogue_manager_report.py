from __future__ import annotations

from collections import Counter

from backend.sales_assistant.service import SalesAssistant


def main() -> int:
    assistant = SalesAssistant()
    queries = (
        "Какие есть туры в сентябре?",
        "Расскажите про Кайлас",
        "Сколько стоит тур на Кайлас?",
        "Хочу консультацию буддолога-психолога",
        "Как связаться с менеджером?",
    )
    replies = [assistant.reply(query, f"report-{index}") for index, query in enumerate(queries)]
    actions = Counter(reply.next_action.value for reply in replies)

    print("AI BODHI — SDM-1 GUIDED SALES DIALOGUE REPORT")
    print(f"Scenarios: {len(replies)}")
    print(f"Manager-required scenarios: {sum(reply.needs_manager for reply in replies)}")
    print("Next actions:")
    for action, count in sorted(actions.items()):
        print(f"- {action}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
