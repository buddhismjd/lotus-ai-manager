from __future__ import annotations

from backend.sales_assistant.product_selection import ProductSelectionService


def main() -> None:
    print("AI BODHI CB-0.9.5 — STATUE & THANGKA SELECTION REPORT")
    for category in ("statue", "thangka"):
        label, url = ProductSelectionService.collection_link(category)
        print(f"- {category}: {label} -> {url}")
    print("- Height constraints: exact, range, approximate")
    print("- Artisan workflow: Telegram/WhatsApp + email")
    print("- Master availability: requires confirmation")


if __name__ == "__main__":
    main()
