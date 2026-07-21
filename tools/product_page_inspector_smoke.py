from __future__ import annotations

from backend.integrations.product_page_inspector import inspect_product_page


def main() -> None:
    inspection = inspect_product_page(
        """
        <html lang="ru"><head>
          <meta property="og:title" content="Ваджра">
          <meta property="og:image" content="https://static.tildacdn.com/vajra.jpg">
          <script type="application/ld+json">
          {"@context":"https://schema.org","@graph":[
            {"@type":"BreadcrumbList","itemListElement":[
              {"@type":"ListItem","position":1,"name":"Магазин"},
              {"@type":"ListItem","position":2,"name":"Алтарь"}]},
            {"@type":"Product","name":"Ваджра","material":"бронза",
             "offers":{"@type":"Offer","price":"25000","priceCurrency":"RUB",
             "availability":"https://schema.org/OutOfStock"}}
          ]}
          </script>
        </head><body><h1>Ваджра</h1><p>Материал: бронза. Высота: 12 см. Нет в наличии.</p></body></html>
        """,
        "https://svet-lotosa.tilda.ws/tproduct/296122659532-vadzhra",
    )
    assert inspection.images
    assert inspection.breadcrumb_candidates
    assert any(item.field == "availability" for item in inspection.evidence)
    print("SMOKE PASSED")
    print(f"Evidence: {len(inspection.evidence)}")
    print(f"Images: {len(inspection.images)}")
    print(f"Breadcrumbs: {len(inspection.breadcrumb_candidates)}")


if __name__ == "__main__":
    main()
