from __future__ import annotations

import json

from backend.catalog.integrity.raw_snapshot_comparator import compare_product_objects
from backend.integrations.product_raw_snapshot import build_raw_snapshot
from backend.integrations.product_snapshot_storage import save_raw_snapshot
from backend.storage import database


HTML = '''
<html><script>
var product = {
  "uid": 101,
  "title": "Ваджра",
  "brand": "Тибет",
  "unknown_future_field": {"master": "A"},
  "gallery": [{"img": "one.jpg"}],
  "quantity": "0"
};
</script></html>
'''


def test_comparator_detects_field_lost_from_snapshot() -> None:
    comparison = compare_product_objects(
        product_uid="101",
        page_url="https://example.test/101",
        page_data={"uid": 101, "brand": "Тибет", "title": "Ваджра"},
        stored_data={"uid": 101, "title": "Ваджра"},
    )

    assert comparison.integrity_percent < 100
    assert any(
        item.path == "brand" and item.kind == "lost_from_snapshot"
        for item in comparison.differences
    )


def test_comparator_reports_identical_complete_object() -> None:
    product = {
        "uid": 101,
        "brand": "Тибет",
        "nested": {"value": 1},
        "gallery": [{"img": "one.jpg"}],
    }
    comparison = compare_product_objects(
        product_uid="101",
        page_url="https://example.test/101",
        page_data=product,
        stored_data=product,
    )

    assert comparison.is_identical
    assert comparison.integrity_percent == 100.0


def test_raw_snapshot_preserves_unknown_fields_and_source_metadata() -> None:
    snapshot = build_raw_snapshot(HTML, "https://example.test/101")

    assert snapshot.product_data["brand"] == "Тибет"
    assert snapshot.product_data["unknown_future_field"] == {"master": "A"}
    assert json.loads(snapshot.raw_json)["unknown_future_field"] == {"master": "A"}
    assert snapshot.source_kind == "product_page_script"
    assert snapshot.extractor_version == "2.2"


def test_storage_preserves_full_raw_json_and_metadata(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "integrity.db"
    monkeypatch.setattr(database, "DATABASE_FILE", db_path)
    database.initialize_database()

    snapshot = build_raw_snapshot(HTML, "https://example.test/101")
    save_raw_snapshot(snapshot)

    with database.get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM product_raw_snapshots WHERE product_uid = '101'"
        ).fetchone()

    stored = json.loads(row["raw_json"])
    assert stored["brand"] == "Тибет"
    assert stored["unknown_future_field"] == {"master": "A"}
    assert row["source_kind"] == "product_page_script"
    assert row["extractor_version"] == "2.2"


def test_raw_snapshot_selects_uid_from_tproduct_url() -> None:
    html = """
    <script>var product = {"uid": 111, "title": "Другой", "quantity": "4"};</script>
    <script>var product = {"uid": 222, "title": "Нужный", "quantity": "0"};</script>
    """
    snapshot = build_raw_snapshot(html, "https://example.test/tproduct/222-needed")
    assert snapshot.product_uid == "222"
    assert snapshot.product_data["title"] == "Нужный"
