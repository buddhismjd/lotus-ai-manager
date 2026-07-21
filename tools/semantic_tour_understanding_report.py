from __future__ import annotations

from backend.sales_assistant.tour_discovery import (
    ASPECT_ALIASES,
    NATURAL_TIME_ALIASES,
)


def main() -> None:
    print("AI BODHI CB-0.9.2 — SEMANTIC TOUR UNDERSTANDING REPORT")
    print("Commercial domain: tours")
    print("Supported aspect groups:")
    for label in ASPECT_ALIASES:
        print(f"- {label}")
    print("Supported natural time expressions:")
    for label in NATURAL_TIME_ALIASES:
        print(f"- {label}")
    print("Mandatory time/trekking/difficulty questions: 0")


if __name__ == "__main__":
    main()
