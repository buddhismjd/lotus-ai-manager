from __future__ import annotations

from backend.integrations.product_page_snapshot import parse_product_page


def main() -> None:
    snapshot = parse_product_page(
        """
        <html><head><meta property='og:image' content='https://example.com/item.jpg'>
        <script type='application/ld+json'>
        {"@type":"Product","material":"бронза","offers":{"availability":"https://schema.org/OutOfStock"}}
        </script></head><body>Нет в наличии</body></html>
        """,
        "https://example.com/product",
    )
    assert snapshot.image_url == "https://example.com/item.jpg"
    assert snapshot.availability_status == "Нет в наличии"
    assert snapshot.material == "бронза"
    print("SMOKE PASSED")


if __name__ == "__main__":
    main()
