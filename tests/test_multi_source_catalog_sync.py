from dataclasses import replace

from backend.integrations.product_catalog_sources import extract_product_uids
from backend.integrations.catalog_completeness import build_catalog_completeness_report
from backend.integrations.tilda_store_api import StoreProduct


def product(uid: str, category: str = "") -> StoreProduct:
    return StoreProduct(uid=uid,title=f"P{uid}",description="",price="",currency="",sku="",url=f"https://x/tproduct/{uid}-x",category=category,image_url="",raw={})


def test_extracts_product_uids_from_tilda_links_and_attributes():
    html='''<a href="/tproduct/123456-statue"></a><div data-product-uid="789012"></div>'''
    assert extract_product_uids(html) == {"123456", "789012"}


def test_completeness_fails_when_required_source_page_failed():
    Source = type("Source", (), {})
    ok = Source(); ok.required=True; ok.error=None; ok.html_loaded=True
    failed = Source(); failed.required=True; failed.error="boom"; failed.html_loaded=False
    report = build_catalog_completeness_report([product("1","Статуи")], [], configured_store_blocks=1, source_reports=[ok, failed])
    assert report.complete is False
    assert report.source_pages_checked == 2
    assert report.source_pages_failed == 1
