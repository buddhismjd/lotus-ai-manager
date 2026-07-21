from __future__ import annotations

from backend.sales_assistant.dialogue import NextActionType
from backend.sales_assistant.service import SalesAssistant, SalesReply


def main() -> None:
    assistant = SalesAssistant()
    reply = assistant._with_dialogue(
        SalesReply(
            answer="Карточка без открытого URL.",
            kind="tour",
            topic="tour",
            title="Тибет + Кайлас",
            url="https://example.com/kailas",
        ),
        "tour_details",
    )
    links = [item for item in reply.suggestions if item.action == NextActionType.OPEN_URL]
    print("AI BODHI CB-0.9.4 DIAGNOSTICS")
    print(f"Raw URL in answer: {'https://' in reply.answer}")
    print(f"URL buttons: {len(links)}")
    print(f"Button URL: {links[0].url if links else 'missing'}")


if __name__ == "__main__":
    main()
