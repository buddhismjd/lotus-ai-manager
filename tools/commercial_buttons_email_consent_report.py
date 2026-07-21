from __future__ import annotations

from backend.sales_assistant.dialogue import SalesDialogueManager


def main() -> None:
    manager = SalesDialogueManager()
    for topic in ("tour", "product", "psychologist"):
        plan = manager.plan(
            strategy="tour_details" if topic == "tour" else "product_search",
            topic=topic,
            kind=topic,
            title="Пример",
        )
        email = [item.label for item in plan.suggestions if "email" in item.label.casefold()]
        print(f"{topic}: {email[0] if email else 'no email action'}")


if __name__ == "__main__":
    main()
