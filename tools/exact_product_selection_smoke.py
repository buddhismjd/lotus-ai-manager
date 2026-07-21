from backend.sales_assistant.product_selection import ProductSelectionRequest
from backend.sales_assistant.selection_page import build_selection_url


def main() -> None:
    request = ProductSelectionRequest("statue", "статуи", "Будда", 10, 14)
    url = build_selection_url(request)
    assert "category=statue" in url
    assert "height_min_cm=10" in url
    assert "height_max_cm=14" in url
    print("SMOKE PASSED")


if __name__ == "__main__":
    main()
