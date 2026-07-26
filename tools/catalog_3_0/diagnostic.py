try:
    from ._bootstrap import ensure_project_root
except ImportError:  # direct file execution
    from _bootstrap import ensure_project_root

ensure_project_root()

from backend.tours.collection_builder import build_tour_collection


def main() -> None:
    items = build_tour_collection("Что по Индии?")
    titles = [item.title for item in items]
    expected_fragments = ("Куллу", "Ладакх", "Маркха")
    missing = [fragment for fragment in expected_fragments if not any(fragment in title for title in titles)]
    print(f"CATALOG-3.0 India collection: {len(items)} item(s)")
    for title in titles:
        print(f"- {title}")
    if missing:
        raise SystemExit(f"FAILED: missing India tours: {', '.join(missing)}")
    print("CATALOG-3.0 diagnostic: OK")


if __name__ == "__main__":
    main()
