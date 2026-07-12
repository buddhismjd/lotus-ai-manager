from __future__ import annotations

from backend.sales_assistant.dialogue import NextActionType
from backend.sales_assistant.service import SalesAssistant


def main() -> int:
    reply = SalesAssistant().reply("Сколько стоит тур на Кайлас?", "sdm-smoke")

    assert reply.kind == "tour_price"
    assert reply.next_action == NextActionType.LEAVE_CONTACT
    assert reply.needs_manager
    assert reply.suggestions

    print("SMOKE PASSED")
    print(f"Next action: {reply.next_action.value}")
    print(f"Suggestions: {len(reply.suggestions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
