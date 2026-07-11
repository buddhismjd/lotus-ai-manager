from __future__ import annotations

from backend.catalog.aspect_catalog import (
    list_aspect_groups,
)


def main() -> None:
    groups = list_aspect_groups()

    print("=" * 72)
    print("AI BODHI ASPECT KNOWLEDGE REPORT")
    print("=" * 72)
    print(f"Аспектов в каталоге: {len(groups)}")

    for group in groups:
        print(f"\n{group.aspect}")

        for label, products in group.by_type.items():
            print(f"  {label}: {len(products)}")

            for product in products[:5]:
                print(f"    - {product.title}")

            if len(products) > 5:
                print(
                    f"    ... ещё {len(products) - 5}"
                )


if __name__ == "__main__":
    main()
