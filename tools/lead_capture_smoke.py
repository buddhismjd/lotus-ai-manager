from backend.sales_assistant.service import SalesAssistant

def main() -> None:
    assistant = SalesAssistant()
    reply = assistant.reply("Хочу оставить контакт для связи", "smoke")
    assert reply.kind == "lead_capture"
    assert reply.dialogue_stage == "lead_name"
    print("SMOKE PASSED")

if __name__ == "__main__":
    main()
