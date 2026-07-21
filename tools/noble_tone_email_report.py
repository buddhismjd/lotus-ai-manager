from __future__ import annotations

from backend.sales_assistant.dialogue import NextActionType, SalesDialogueManager


def main() -> None:
    manager = SalesDialogueManager()
    topics = (
        ("tour", "tour", "Тибет + Кайлас"),
        ("product", "product", "Ваджра"),
        ("psychologist", "psychologist", "Консультация психолога-буддолога"),
    )
    print("AI BODHI CB-0.9.3 REPORT")
    for topic, kind, title in topics:
        plan = manager.plan(strategy=f"{topic}_details", topic=topic, kind=kind, title=title)
        enabled = any(item.action == NextActionType.EMAIL_FOLLOWUP for item in plan.suggestions)
        print(f"- {topic}: email_followup={enabled}")
    print("Tone: noble, warm, respectful")
    print("Email scope: requested information only")


if __name__ == "__main__":
    main()
