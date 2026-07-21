from __future__ import annotations

from backend.catalog.integrity.raw_snapshot_comparator import compare_product_objects


def main() -> int:
    page = {"uid": 1, "title": "Товар", "brand": "Тибет"}
    stored = {"uid": 1, "title": "Товар", "brand": "Тибет"}
    result = compare_product_objects(
        product_uid="1",
        page_url="https://example.test/1",
        page_data=page,
        stored_data=stored,
    )
    if not result.is_identical or result.integrity_percent != 100.0:
        raise SystemExit("SMOKE FAILED")
    print("SMOKE PASSED")
    print("Source integrity: 100.00%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
