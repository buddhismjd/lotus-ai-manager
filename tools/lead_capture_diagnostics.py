from backend.sales_assistant.service import SalesAssistant

def main() -> None:
    assistant = SalesAssistant()
    first = assistant.reply("Расскажите про Кайлас", "diagnostic")
    second = assistant.reply("Хочу оставить заявку", "diagnostic")
    third = assistant.reply("Евгения", "diagnostic")
    print("AI BODHI SDM-3 LEAD CAPTURE DIAGNOSTICS")
    print(f"Context tour: {first.title}")
    print(f"Start stage: {second.dialogue_stage}")
    print(f"Next stage: {third.dialogue_stage}")
    print(f"Random tour leakage: {'Занскар' in third.answer}")

if __name__ == "__main__":
    main()
