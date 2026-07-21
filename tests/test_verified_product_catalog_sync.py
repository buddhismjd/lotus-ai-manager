from __future__ import annotations

from decimal import Decimal

from backend.integrations.product_page_snapshot import parse_product_page
from backend.integrations import product_catalog_synchronizer as synchronizer
from backend.integrations.tilda_store_api import StoreProduct


def test_product_page_snapshot_uses_published_schema_data() -> None:
    source = """
    <html><head>
      <meta property="og:image" content="//static.tildacdn.com/vajra.jpg">
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Ваджра",
        "image": "https://static.tildacdn.com/vajra-schema.jpg",
        "description": "Ритуальный предмет. Материал: бронза.",
        "material": "бронза",
        "offers": {
          "@type": "Offer",
          "price": "25000",
          "priceCurrency": "RUB",
          "availability": "https://schema.org/OutOfStock"
        }
      }
      </script>
    </head><body><div>Нет в наличии</div></body></html>
    """

    snapshot = parse_product_page(
        source,
        "https://svet-lotosa.tilda.ws/tproduct/296122659532-vadzhra",
    )

    assert snapshot.image_url == "https://static.tildacdn.com/vajra-schema.jpg"
    assert snapshot.availability_status == "Нет в наличии"
    assert snapshot.material == "бронза"
    assert snapshot.price == Decimal("25000")
    assert snapshot.currency == "RUB"


def test_visible_status_is_used_when_schema_has_no_offer() -> None:
    snapshot = parse_product_page(
        """
        <html><head><meta property="og:image" content="/image.jpg"></head>
        <body><h1>Статуя</h1><div class="status">Под заказ</div></body></html>
        """,
        "https://svet-lotosa.tilda.ws/product",
    )

    assert snapshot.image_url == "https://svet-lotosa.tilda.ws/image.jpg"
    assert snapshot.availability_status == "Под заказ"


def test_unknown_status_is_not_invented() -> None:
    snapshot = parse_product_page(
        "<html><body><h1>Статуя</h1></body></html>",
        "https://svet-lotosa.tilda.ws/product",
    )

    assert snapshot.availability_status is None


def test_page_snapshot_overrides_stale_store_api_values(monkeypatch) -> None:
    product = StoreProduct(
        uid="296122659532",
        title="Ваджра",
        description="Старое описание",
        price="100",
        currency="RUB",
        sku="Vajra",
        url="https://svet-lotosa.tilda.ws/tproduct/296122659532-vadzhra",
        category="Алтарь",
        image_url="",
        availability_status="В наличии",
        material=None,
        raw={},
    )

    monkeypatch.setattr(
        synchronizer,
        "load_product_page_snapshot",
        lambda url: parse_product_page(
            """
            <html><head>
              <meta property="og:image" content="https://static.tildacdn.com/vajra.jpg">
              <script type="application/ld+json">
              {"@type":"Product","material":"медь","offers":{
                "price":"25000","priceCurrency":"RUB",
                "availability":"https://schema.org/OutOfStock"}}
              </script>
            </head><body>Нет в наличии</body></html>
            """,
            url,
        ),
    )

    enriched = synchronizer._enrich(product)

    assert enriched.image_url == "https://static.tildacdn.com/vajra.jpg"
    assert enriched.availability_status == "Нет в наличии"
    assert enriched.material == "медь"
    assert enriched.price == "25000"
