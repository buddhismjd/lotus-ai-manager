from __future__ import annotations

from backend.sales_assistant.service import SalesAssistant


CASES = (
    ("Какие есть туры в сентябре?", "tour_list"),
    ("Помогите подобрать подходящий тур", "tour_selection"),
    ("Расскажите про Кайлас", "tour"),
    ("А сколько стоит?", "tour_price"),
)


def main() -> None:
    assistant = SalesAssistant()
    session = "report"
    print("AI BODHI SDM-2 — DIALOGUE STATE REPORT")
    passed = 0
    for query, expected in CASES:
        reply = assistant.reply(query, session)
        ok = reply.kind == expected
        passed += int(ok)
        print(f"[{'OK' if ok else 'FAIL'}] {query} -> {reply.kind}")
    print(f"Passed scenarios: {passed}/{len(CASES)}")


if __name__ == "__main__":
    main()
