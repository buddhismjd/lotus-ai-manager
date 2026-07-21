from __future__ import annotations

from backend.sales_assistant.product_selection import parse_product_selection_request


def main() -> None:
    request = parse_product_selection_request("Статуя Ченрезига 15-20 см")
    assert request is not None
    print("=" * 72)
    print("AI BODHI STATUE & THANGKA SELECTION DIAGNOSTICS")
    print("=" * 72)
    print(f"Category: {request.category}")
    print(f"Aspect: {request.aspect}")
    print(f"Height range: {request.height_label}")
    print("Contact workflow: social contact + email")
    print("Availability promise: prohibited until master confirmation")


if __name__ == "__main__":
    main()
