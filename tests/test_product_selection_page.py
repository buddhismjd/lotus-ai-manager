from __future__ import annotations

from backend.sales_assistant.product_selection import ProductSelectionRequest
from backend.sales_assistant.selection_page import build_selection_url


def test_selection_url_contains_exact_request() -> None:
    request = ProductSelectionRequest(
        category="statue",
        category_label="статуи",
        aspect="Будда",
        height_min_cm=10,
        height_max_cm=14,
    )
    url = build_selection_url(request)
    assert url.startswith("/api/sales/product-selection?")
    assert "category=statue" in url
    assert "%D0%91%D1%83%D0%B4%D0%B4%D0%B0" in url
    assert "height_min_cm=10" in url
    assert "height_max_cm=14" in url
