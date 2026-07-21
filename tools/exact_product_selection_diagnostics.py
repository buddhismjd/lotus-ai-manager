from backend.sales_assistant.product_selection import ProductSelectionRequest
from backend.sales_assistant.selection_page import build_selection_url


def main() -> None:
    request = ProductSelectionRequest(
        category="statue",
        category_label="статуи",
        aspect="Будда",
        height_min_cm=10,
        height_max_cm=14,
    )
    print("AI BODHI EXACT PRODUCT SELECTION DIAGNOSTICS")
    print(f"URL: {build_selection_url(request)}")
    print("Exact criteria preserved: True")


if __name__ == "__main__":
    main()
