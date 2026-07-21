from __future__ import annotations

from backend.sales_assistant.product_selection import parse_product_selection_request


def main() -> None:
    request = parse_product_selection_request("Есть статуя Ченрезига 15–20 см?")
    assert request is not None
    assert request.category == "statue"
    assert request.aspect == "Ченрезиг"
    assert request.height_min_cm == 15
    assert request.height_max_cm == 20
    print("SMOKE PASSED")
    print("Statue height request resolved without guessing.")


if __name__ == "__main__":
    main()
