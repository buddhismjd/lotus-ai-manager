from __future__ import annotations

import hashlib
import json
from typing import Any

from backend.catalog.product_intelligence import analyze_product
from backend.catalog.product_profiles import (
    ProductProfile,
    get_profile_stats,
    initialize_product_profiles,
    save_product_profile,
)
from backend.integrations.tilda_store_api import (
    DEFAULT_RECID,
    DEFAULT_STORE_PART_UID,
    StoreProduct,
    fetch_all_products,
)


TYPE_SYNONYMS: dict[str, tuple[str, ...]] = {
    "statue": ("статуя", "статуэтка", "скульптура", "образ"),
    "thangka": ("тханка", "танка", "буддийская живопись"),
    "singing_bowl": ("поющая чаша", "тибетская чаша", "чаша"),
    "amulet": ("амулет", "оберег", "подвеска", "кулон"),
    "mala": ("чётки", "четки", "мала"),
    "vajra": ("ваджра", "дордже", "ритуальный предмет"),
    "incense": ("благовония", "аромапалочки"),
    "jewelry": ("украшение", "ювелирное изделие"),
    "ritual_item": ("ритуальный предмет",),
}

TRADITION_PATTERNS: dict[str, tuple[str, ...]] = {
    "Ваджраяна": (
        "ваджраяна",
        "тибетский буддизм",
        "тантрический",
        "тантрическая",
    ),
    "Махаяна": (
        "махаяна",
        "бодхисаттва",
    ),
}


def _normalize(text: str) -> str:
    return (text or "").lower().replace("ё", "е")


def _detect_traditions(text: str) -> tuple[str, ...]:
    normalized = _normalize(text)

    return tuple(
        tradition
        for tradition, aliases in TRADITION_PATTERNS.items()
        if any(_normalize(alias) in normalized for alias in aliases)
    )


def build_product_profile(product: StoreProduct) -> ProductProfile:
    intelligence = analyze_product(
        title=product.title,
        description=product.description,
        category=product.category,
        sku=product.sku,
    )

    entities = tuple(dict.fromkeys(intelligence.entities))
    primary_entity = entities[0] if entities else None

    synonyms = TYPE_SYNONYMS.get(
        intelligence.product_type or "",
        (),
    )

    keywords = tuple(
        dict.fromkeys(
            [
                *intelligence.keywords,
                *synonyms,
                product.category,
                product.sku,
            ]
        )
    )
    keywords = tuple(
        keyword
        for keyword in keywords
        if keyword and str(keyword).strip()
    )

    source_hash = hashlib.sha256(
        json.dumps(
            product.raw,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()

    return ProductProfile(
        product_id=f"product-{product.uid}",
        product_type=intelligence.product_type,
        primary_entity=primary_entity,
        entities=entities,
        materials=tuple(dict.fromkeys(intelligence.materials)),
        usages=tuple(dict.fromkeys(intelligence.usages)),
        traditions=_detect_traditions(
            " ".join(
                [
                    product.title,
                    product.description,
                    product.category,
                ]
            )
        ),
        synonyms=tuple(dict.fromkeys(synonyms)),
        keywords=keywords,
        source_hash=source_hash,
    )


def sync_catalog_intelligence(
    *,
    storepartuid: str = DEFAULT_STORE_PART_UID,
    recid: str = DEFAULT_RECID,
) -> dict[str, Any]:
    initialize_product_profiles()

    products, metadata = fetch_all_products(
        storepartuid=storepartuid,
        recid=recid,
    )

    saved = 0
    errors: list[dict[str, str]] = []

    for product in products:
        try:
            save_product_profile(build_product_profile(product))
            saved += 1
        except Exception as exc:
            errors.append(
                {
                    "uid": product.uid,
                    "title": product.title,
                    "error": str(exc),
                }
            )

    return {
        **metadata,
        "profiles_saved": saved,
        "errors_count": len(errors),
        "errors": errors,
        "profile_stats": get_profile_stats(),
    }


def print_summary(result: dict[str, Any]) -> None:
    stats = result.get("profile_stats") or {}

    print("=" * 72)
    print("AI BODHI CATALOG INTELLIGENCE V2")
    print("=" * 72)
    print(f"Products received: {result.get('received_total', 0)}")
    print(f"Profiles saved:    {result.get('profiles_saved', 0)}")
    print(f"Errors:            {result.get('errors_count', 0)}")
    print(f"Typed profiles:    {stats.get('typed', 0)}")
    print(f"Unknown type:      {stats.get('unknown_type', 0)}")
    print(f"With entity:       {stats.get('with_entity', 0)}")

    by_type = stats.get("by_type") or {}

    if by_type:
        print("\nProfiles by type:")

        for product_type, count in by_type.items():
            print(f"  {product_type}: {count}")

    errors = result.get("errors") or []

    if errors:
        print("\nErrors:")

        for error in errors:
            print(
                f"- {error.get('uid')} "
                f"{error.get('title')}: "
                f"{error.get('error')}"
            )


if __name__ == "__main__":
    print_summary(sync_catalog_intelligence())
