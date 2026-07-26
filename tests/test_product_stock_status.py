from backend.integrations.product_page_snapshot import parse_product_page
from backend.integrations.product_raw_snapshot import RawProductSnapshot
from backend.integrations.product_snapshot_normalizer import normalize_raw_snapshot
from backend.integrations.product_stock_status import resolve_stock_status


def test_zero_quantity_is_out_of_stock_even_with_generic_in_stock_text():
    html = '''<html><body><div>В наличии</div><script>var product = {"uid":"1","title":"Статуя","quantity":"0"};</script></body></html>'''
    snapshot = parse_product_page(html, "https://example.test/tproduct/1")
    assert snapshot.availability_status == "Нет в наличии"


def test_positive_quantity_is_in_stock():
    assert resolve_stock_status(quantity="2") == "В наличии"


def test_normalized_snapshot_persists_quantity_derived_status():
    raw = RawProductSnapshot(
        product_uid="1", page_url="https://example.test/tproduct/1",
        product_data={"uid":"1", "title":"Статуя", "quantity":"0"},
        raw_json='{"uid":"1","title":"Статуя","quantity":"0"}',
        html_sha256="h", snapshot_sha256="s", captured_at="2026-07-22T00:00:00+00:00",
    )
    normalized = normalize_raw_snapshot(raw)
    assert normalized.quantity == 0
    assert normalized.availability_status == "Нет в наличии"


def test_generic_page_in_stock_label_is_not_product_stock_truth():
    html = '<html><body><div>В наличии</div></body></html>'
    snapshot = parse_product_page(html, "https://example.test/tproduct/1")
    assert snapshot.availability_status is None


def test_page_parser_selects_product_object_matching_url_uid():
    html = """
    <html><body>
    <script>var product = {"uid":"111","title":"Другой","quantity":"5"};</script>
    <script>var product = {"uid":"222","title":"Нужный","quantity":"0"};</script>
    </body></html>
    """
    snapshot = parse_product_page(html, "https://example.test/tproduct/222-needed")
    assert snapshot.availability_status == "Нет в наличии"


def test_visible_preorder_label_overrides_tilda_zero_quantity():
    html = '''
    <html><body>
      <div class="product-status">Под заказ</div>
      <script>var product = {"uid":"77","title":"Подвеска","quantity":"0"};</script>
    </body></html>
    '''
    snapshot = parse_product_page(html, "https://example.test/tproduct/77-pendant")
    assert snapshot.availability_status == "Под заказ"
