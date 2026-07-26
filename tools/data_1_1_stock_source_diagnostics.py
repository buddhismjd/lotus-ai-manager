from backend.integrations.product_page_snapshot import parse_product_page
from backend.integrations.product_raw_snapshot import build_raw_snapshot


def main() -> None:
    html = '''
    <html><body>
      <div>В наличии</div>
      <script>var product = {"uid":"111","title":"Другой товар","quantity":"5"};</script>
      <script>var product = {"uid":"222","title":"Проверяемый товар","quantity":"0"};</script>
    </body></html>
    '''
    url = "https://example.test/tproduct/222-proveryaemyy-tovar"
    raw = build_raw_snapshot(html, url)
    page = parse_product_page(html, url)

    assert raw.product_uid == "222"
    assert raw.product_data["title"] == "Проверяемый товар"
    assert page.availability_status == "Нет в наличии"

    generic = parse_product_page(
        "<html><body><div>В наличии</div></body></html>",
        "https://example.test/tproduct/333-generic",
    )
    assert generic.availability_status is None
    print("DATA-1.1 diagnostic: PASS")


if __name__ == "__main__":
    main()
