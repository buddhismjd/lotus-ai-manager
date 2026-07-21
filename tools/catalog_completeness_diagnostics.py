from backend.integrations.product_catalog_synchronizer import print_summary, sync_product_catalog


def main() -> None:
    result = sync_product_catalog()
    print_summary(result)
    completeness = result["completeness"]
    if not completeness.complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
