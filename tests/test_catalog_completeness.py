from backend.integrations.catalog_completeness import build_catalog_completeness_report
from backend.integrations.tilda_store_api import StoreProduct
from backend.integrations.tilda_store_multi_sync import StorePartResult


def product(uid: str, category: str = "Статуи") -> StoreProduct:
    return StoreProduct(uid, f"Товар {uid}", "", "", "", "", f"https://example/{uid}", category, "", {})


def test_complete_multiple_store_blocks_and_categories() -> None:
    report = build_catalog_completeness_report(
        [product("1", "Статуи"), product("2", "Гау"), product("3", "Статуи")],
        [
            StorePartResult("a", "1", 2, 2, 1, unique_added=2),
            StorePartResult("b", "2", 1, 1, 1, unique_added=1),
        ],
        configured_store_blocks=2,
    )
    assert report.complete is True
    assert report.unique_products == 3
    assert report.category_counts == {"Гау": 1, "Статуи": 2}


def test_incomplete_block_is_reported() -> None:
    report = build_catalog_completeness_report(
        [product("1")],
        [StorePartResult("a", "1", 5, 1, 1, unique_added=1)],
        configured_store_blocks=1,
    )
    assert report.complete is False
    assert any("Неполный блок" in warning for warning in report.warnings)


def test_duplicate_across_blocks_is_visible_but_not_fatal() -> None:
    report = build_catalog_completeness_report(
        [product("1")],
        [
            StorePartResult("a", "1", 1, 1, 1, unique_added=1),
            StorePartResult("b", "2", 1, 1, 1, unique_added=0, duplicates=1),
        ],
        configured_store_blocks=2,
        duplicate_products_across_blocks=1,
    )
    assert report.complete is True
    assert report.duplicate_products_across_blocks == 1
    assert any("нескольких блоках" in warning for warning in report.warnings)
