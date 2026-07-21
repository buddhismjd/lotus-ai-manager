from backend.integrations.product_catalog_synchronizer import sync_product_catalog


def main() -> None:
    result = sync_product_catalog()
    report = result["completeness"]
    print("AI BODHI CATALOG COMPLETENESS REPORT")
    print(f"Store blocks configured: {report.configured_store_blocks}")
    print(f"Store blocks successful: {report.successful_store_blocks}")
    print(f"Unique products: {report.unique_products}")
    print(f"Expected across blocks: {report.expected_products_total}")
    print(f"Received across blocks: {report.received_products_total}")
    print("Categories:")
    for category, count in report.category_counts.items():
        print(f"- {category}: {count}")
    print(f"Complete: {report.complete}")


if __name__ == "__main__":
    main()
