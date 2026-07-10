from __future__ import annotations

from backend.services.knowledge_service import load_knowledge


def main() -> None:
    knowledge = load_knowledge()
    pages = knowledge.get("pages", [])
    errors = knowledge.get("errors", [])

    print("SITE INVENTORY")
    print("=" * 70)
    print(f"Discovered URLs: {knowledge.get('discovered_urls_count', 0)}")
    print(f"Indexed pages:   {len(pages)}")
    print(f"Chunks:          {knowledge.get('chunks_count', 0)}")
    print(f"Errors:          {len(errors)}")
    print()

    counts: dict[str, int] = {}

    for page in pages:
        page_type = page.get("page_type", "general")
        counts[page_type] = counts.get(page_type, 0) + 1

    print("COUNTS BY TYPE")
    for page_type, count in sorted(counts.items()):
        print(f"  {page_type:20} {count}")

    print()
    print("PAGES")
    print("=" * 70)

    for page in sorted(
        pages,
        key=lambda item: (
            item.get("page_type", ""),
            item.get("title", ""),
        ),
    ):
        print(
            f"[{page.get('page_type', 'general')}] "
            f"{page.get('title', 'Без названия')}"
        )
        print(f"  {page.get('url', '')}")

    if errors:
        print()
        print("ERRORS")
        print("=" * 70)

        for error in errors:
            print(error.get("url"))
            print(f"  {error.get('error')}")


if __name__ == "__main__":
    main()
