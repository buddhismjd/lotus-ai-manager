from backend.integrations.catalog_completeness import build_catalog_completeness_report
from backend.integrations.tilda_store_api import StoreProduct
from backend.integrations.tilda_store_multi_sync import StorePartResult


def main() -> None:
    item = StoreProduct("1", "Тест", "", "", "", "", "https://example/1", "Статуи", "", {})
    report = build_catalog_completeness_report(
        [item], [StorePartResult("a", "1", 1, 1, 1, unique_added=1)], configured_store_blocks=1
    )
    assert report.complete
    print("SMOKE PASSED")


if __name__ == "__main__":
    main()
