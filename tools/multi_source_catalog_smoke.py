from backend.integrations.product_catalog_sources import load_catalog_sources


def main() -> None:
    sources = load_catalog_sources()
    assert len(sources) >= 7
    assert any(source.category == "Статуи" for source in sources)
    assert any(source.category == "Благовония" for source in sources)
    print("SMOKE PASSED")
    print(f"Catalog sources: {len(sources)}")


if __name__ == "__main__":
    main()
