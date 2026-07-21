from backend.integrations.product_raw_snapshot import extract_product_object
from backend.integrations.product_snapshot_normalizer import normalize_raw_snapshot
from backend.integrations.product_raw_snapshot import build_raw_snapshot

def main() -> None:
    html = """<script>var product = {"uid":1,"title":"Тест","price":"100","gallery":[{"img":"https://example.test/a.jpg"}],"quantity":"0","characteristics":[],"properties":[],"partuids":[2]};</script>"""
    raw = build_raw_snapshot(html, "https://example.test/tproduct/1-test")
    item = normalize_raw_snapshot(raw)
    assert item.title == "Тест"
    assert item.primary_image == "https://example.test/a.jpg"
    assert item.availability_status is None
    print("SMOKE PASSED")

if __name__ == "__main__":
    main()
