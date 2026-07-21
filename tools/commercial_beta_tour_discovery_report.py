from __future__ import annotations

from backend.sales_assistant.tour_discovery import DIRECTION_ALIASES, DESTINATION_ALIASES


def main() -> None:
    print("AI BODHI COMMERCIAL BETA 0.9.1 — TOUR DISCOVERY REPORT")
    print("Result policy: all matching scheduled tours")
    print("Mandatory questionnaire: disabled")
    print("Month/season prompts: disabled")
    print("Trekking/difficulty prompts: disabled")
    print("Directions:", ", ".join(DIRECTION_ALIASES))
    print("Named destinations:", ", ".join(DESTINATION_ALIASES))


if __name__ == "__main__":
    main()
