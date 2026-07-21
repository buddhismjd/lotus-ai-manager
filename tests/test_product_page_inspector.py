from __future__ import annotations

import json

from backend.integrations.product_page_inspector import (
    inspect_product_page,
    render_text_report,
    write_inspection_bundle,
)


PRODUCT_HTML = """
<html lang="ru"><head>
  <title>Ваджра — Свет Лотоса</title>
  <link rel="canonical" href="/tproduct/296122659532-vadzhra">
  <meta property="og:title" content="Ваджра">
  <meta property="og:image" content="//static.tildacdn.com/vajra-cover.jpg">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@graph":[
    {"@type":"BreadcrumbList","itemListElement":[
      {"@type":"ListItem","position":1,"name":"Магазин"},
      {"@type":"ListItem","position":2,"name":"Алтарь"},
      {"@type":"ListItem","position":3,"name":"Ваджра"}]},
    {"@type":"Product","name":"Ваджра","sku":"VAJRA-1","material":"бронза",
     "image":["https://static.tildacdn.com/vajra-1.jpg"],
     "offers":{"@type":"Offer","price":"25000","priceCurrency":"RUB",
     "availability":"https://schema.org/OutOfStock"}}
  ]}
  </script>
  <script>window.tildaData={productuid:296122659532,storepartuid:123};</script>
</head><body>
  <h1>Ваджра</h1>
  <div class="breadcrumb"><a>Магазин</a><a>Алтарь</a><span>Ваджра</span></div>
  <img data-original="/images/vajra-gallery.jpg" alt="Ваджра">
  <div data-product-uid="296122659532">Материал: бронза. Высота: 12 см. Нет в наличии.</div>
</body></html>
"""


def test_inspector_maps_confirmed_sources() -> None:
    inspection = inspect_product_page(
        PRODUCT_HTML,
        "https://svet-lotosa.tilda.ws/tproduct/296122659532-vadzhra",
    )

    assert inspection.open_graph["og:title"] == "Ваджра"
    assert ["Магазин", "Алтарь", "Ваджра"] in inspection.breadcrumb_candidates
    assert any(item.field == "material" and item.source == "json_ld.Product" for item in inspection.evidence)
    assert any(item.field == "availability" and item.source == "json_ld.Offer" for item in inspection.evidence)
    assert any(item.field == "высота" and item.value == "12 см" for item in inspection.evidence)
    assert any(image.url.endswith("vajra-gallery.jpg") for image in inspection.images)
    assert inspection.data_attributes["data-product-uid"] == ["296122659532"]
    assert inspection.tilda_tokens["productuid"] >= 1


def test_inspector_does_not_invent_missing_fields() -> None:
    inspection = inspect_product_page(
        "<html><body><h1>Товар</h1></body></html>",
        "https://example.test/product",
    )

    assert not any(item.field == "availability" for item in inspection.evidence)
    assert any("Статус наличия" in message for message in inspection.diagnostics)


def test_bundle_contains_raw_html_and_reports(tmp_path) -> None:
    inspection = inspect_product_page(PRODUCT_HTML, "https://example.test/product")
    bundle = write_inspection_bundle(inspection, PRODUCT_HTML, tmp_path)

    assert (bundle / "page.html").read_text(encoding="utf-8") == PRODUCT_HTML
    payload = json.loads((bundle / "inspection.json").read_text(encoding="utf-8"))
    assert payload["url"] == "https://example.test/product"
    report = (bundle / "inspection.txt").read_text(encoding="utf-8")
    assert "CONFIRMED FIELD CANDIDATES" in report
    assert "STRUCTURAL INVENTORY" in report


def test_text_report_marks_absent_values() -> None:
    report = render_text_report(inspect_product_page("<html></html>", "https://example.test/product"))
    assert "availability:" in report
    assert "NOT FOUND" in report
