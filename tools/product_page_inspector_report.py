from __future__ import annotations

from backend.integrations.product_page_inspector import inspect_product_page, render_text_report


def main() -> None:
    inspection = inspect_product_page(
        "<html><head><meta property='og:title' content='Sample'></head><body><h1>Sample</h1></body></html>",
        "https://example.test/product",
    )
    print(render_text_report(inspection))


if __name__ == "__main__":
    main()
