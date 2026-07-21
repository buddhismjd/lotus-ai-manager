from __future__ import annotations

from backend.integrations.tilda_store_discovery import DiscoveryReport
from backend.integrations.tilda_store_multi_sync import StorePartResult


def test_verified_sync_reports_discovery_source(monkeypatch) -> None:
    report = DiscoveryReport(
        shop_url="https://example.test/shop",
        html_loaded=True,
        html_size=100,
        html_candidates=0,
        configured_candidates=1,
        total_candidates=1,
    )
    monkeypatch.setattr(
        "backend.integrations.product_catalog_synchronizer.initialize_database",
        lambda: None,
    )
    monkeypatch.setattr(
        "backend.integrations.product_catalog_synchronizer.fetch_all_discovered_products_with_report",
        lambda: (
            [],
            [StorePartResult("200001", "100001", None, 0, 0, "api failed")],
            report,
        ),
    )

    from backend.integrations.product_catalog_synchronizer import sync_product_catalog

    result = sync_product_catalog()
    assert result["store_blocks"] == 1
    assert result["discovery_report"].configured_candidates == 1
    assert result["success"] is False
