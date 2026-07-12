from backend.sales_assistant.service import SalesAssistant


def main() -> None:
    assistant = SalesAssistant()
    scenarios = (
        "На Кайлас возите?",
        "Есть ли у вас ваджра?",
        "Хочу консультацию буддолога-психолога",
    )
    print("AI BODHI MVP-1.1 — SALES RESPONSE REPORT")
    for index, query in enumerate(scenarios, start=1):
        reply = assistant.reply(query, f"report-{index}")
        print(f"{index}. topic={reply.topic} kind={reply.kind} chars={len(reply.answer)}")


if __name__ == "__main__":
    main()
