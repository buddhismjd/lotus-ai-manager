from __future__ import annotations

from backend.sales_assistant.dialogue import NextActionType, SalesDialogueManager
from backend.sales_assistant.tone import TONE


def main() -> None:
    plan = SalesDialogueManager().plan(
        strategy="tour_details",
        topic="tour",
        kind="tour",
        title="Тибет + Кайлас",
    )
    email_actions = [item for item in plan.suggestions if item.action == NextActionType.EMAIL_FOLLOWUP]
    print("=" * 72)
    print("AI BODHI NOBLE TONE & EMAIL DIAGNOSTICS")
    print("=" * 72)
    print(f"Warm greeting: {'Рада приветствовать' in TONE.greeting}")
    print(f"Email purpose explained: {'только для отправки информации' in TONE.email_request}")
    print(f"Email follow-up actions: {len(email_actions)}")


if __name__ == "__main__":
    main()
