from backend.integrations.product_catalog_synchronizer import sync_product_catalog


def main() -> None:
    result = sync_product_catalog()
    report = result["completeness"]
    discovery = result["discovery_report"]
    print("AI BODHI MULTI-SOURCE CATALOG REPORT")
    print(f"Source pages checked: {report.source_pages_checked}")
    print(f"Source pages failed:  {report.source_pages_failed}")
    print(f"Store blocks:         {len(result['parts'])}")
    print(f"Unique products:      {report.unique_products}")
    print("Categories:")
    for category, count in report.category_counts.items():
        print(f"- {category}: {count}")
    print("Sources:")
    for source in getattr(discovery, "source_reports", ()):
        print(f"- {source.name}: refs={source.product_references}, blocks={source.store_blocks}, loaded={source.html_loaded}")
    print(f"Complete: {report.complete}")


if __name__ == "__main__":
    main()
