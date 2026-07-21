from __future__ import annotations

from types import SimpleNamespace

from backend.sales_assistant.service import SalesAssistant


class MemoryLeads:
    def __init__(self) -> None:
        self.payload = None

    def save(self, **payload):
        self.payload = payload
        return SimpleNamespace(id=1)


def main() -> None:
    assistant = SalesAssistant()
    leads = MemoryLeads()
    assistant._leads = leads  # type: ignore[assignment]
    state = assistant._states.get("smoke")
    state.topic = "product"
    state.active_title = "Ваджра"
    state.last_query = "Есть ли Ваджра?"
    assistant.reply("Отправьте, пожалуйста, информацию на email", "smoke")
    result = assistant.reply("smoke@example.com", "smoke")
    assert result.kind == "email_saved"
    assert leads.payload["interest"] == "Ваджра"
    print("SMOKE PASSED")
    print("Interest: Ваджра")
    print("Email purpose: information follow-up")


if __name__ == "__main__":
    main()
