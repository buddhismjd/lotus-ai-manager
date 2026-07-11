from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from backend.catalog.product_intelligence import analyze_product
from backend.catalog.product_profiles import (
    ProductProfile,
    get_profile_stats,
    initialize_product_profiles,
    save_product_profile,
)
from backend.catalog.repositories import ProductRepository


PRODUCT_UID_RE = re.compile(
    r"/tproduct/(?P<uid>\d+)",
    re.IGNORECASE,
)

TYPE_SYNONYMS: dict[str, tuple[str, ...]] = {
    "statue": ("статуя", "статуэтка", "скульптура", "образ"),
    "thangka": ("тханка", "танка", "буддийская живопись"),
    "singing_bowl": ("поющая чаша", "тибетская чаша", "чаша"),
    "bowl": ("поющая чаша", "тибетская чаша", "чаша"),
    "amulet": ("амулет", "оберег", "подвеска", "кулон", "гау"),
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


def _product_profile_id(product: Any) -> str:
    url = str(getattr(product, "url", "") or "")
    match = PRODUCT_UID_RE.search(url)

    if match:
        return f"product-{match.group('uid')}"

    source_id = str(
        getattr(product, "source_id", "")
        or getattr(product, "id", "")
        or ""
    ).strip()

    if source_id:
        if source_id.startswith("product-"):
            return source_id
        return f"product-{source_id}"

    stable_source = "|".join(
        [
            str(getattr(product, "title", "") or ""),
            url,
        ]
    )
    digest = hashlib.sha256(
        stable_source.encode("utf-8")
    ).hexdigest()[:20]
    return f"product-local-{digest}"


def _detect_traditions(text: str) -> tuple[str, ...]:
    normalized = _normalize(text)

    return tuple(
        tradition
        for tradition, aliases in TRADITION_PATTERNS.items()
        if any(_normalize(alias) in normalized for alias in aliases)
    )


def build_repository_product_profile(product: Any) -> ProductProfile:
    title = str(getattr(product, "title", "") or "")
    description = str(getattr(product, "description", "") or "")
    category = str(getattr(product, "category", "") or "")
    sku = str(getattr(product, "sku", "") or "")
    material = str(getattr(product, "material", "") or "")
    repository_keywords = tuple(
        str(value)
        for value in (getattr(product, "keywords", []) or [])
        if str(value).strip()
    )

    intelligence = analyze_product(
        title=title,
        description=description,
        category=category,
        sku=sku,
    )

    entities = tuple(dict.fromkeys(intelligence.entities))
    primary_entity = entities[0] if entities else None
    synonyms = TYPE_SYNONYMS.get(
        intelligence.product_type or "",
        (),
    )

    keywords = tuple(
        dict.fromkeys(
            value
            for value in [
                *intelligence.keywords,
                *repository_keywords,
                *synonyms,
                category,
                sku,
            ]
            if value and str(value).strip()
        )
    )

    source_payload = {
        "title": title,
        "description": description,
        "category": category,
        "sku": sku,
        "material": material,
        "keywords": repository_keywords,
        "url": str(getattr(product, "url", "") or ""),
    }
    source_hash = hashlib.sha256(
        json.dumps(
            source_payload,
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    materials = tuple(
        dict.fromkeys(
            [
                *intelligence.materials,
                *([material] if material else []),
            ]
        )
    )

    return ProductProfile(
        product_id=_product_profile_id(product),
        product_type=intelligence.product_type,
        primary_entity=primary_entity,
        entities=entities,
        materials=materials,
        usages=tuple(dict.fromkeys(intelligence.usages)),
        traditions=_detect_traditions(
            " ".join([title, description, category])
        ),
        synonyms=tuple(dict.fromkeys(synonyms)),
        keywords=keywords,
        source_hash=source_hash,
    )


def sync_repository_catalog_intelligence() -> dict[str, Any]:
    """
    Build profiles from the merged ProductRepository.

    This is intentional: the repository already combines YML products and
    products imported from the statues Store API. Building profiles from one
    Store API block alone would classify only that category.
    """
    initialize_product_profiles()
    products = ProductRepository().list_all()

    saved = 0
    errors: list[dict[str, str]] = []
    profile_ids: set[str] = set()

    for product in products:
        try:
            profile = build_repository_product_profile(product)
            save_product_profile(profile)
            profile_ids.add(profile.product_id)
            saved += 1
        except Exception as exc:
            errors.append(
                {
                    "title": str(getattr(product, "title", "") or ""),
                    "url": str(getattr(product, "url", "") or ""),
                    "error": str(exc),
                }
            )

    return {
        "repository_products": len(products),
        "unique_profile_ids": len(profile_ids),
        "profiles_saved": saved,
        "errors_count": len(errors),
        "errors": errors,
        "profile_stats": get_profile_stats(),
    }


def print_summary(result: dict[str, Any]) -> None:
    stats = result.get("profile_stats") or {}

    print("=" * 72)
    print("AI BODHI REPOSITORY CATALOG INTELLIGENCE")
    print("=" * 72)
    print(
        f"Repository products: {result.get('repository_products', 0)}"
    )
    print(
        f"Unique profile IDs:  {result.get('unique_profile_ids', 0)}"
    )
    print(
        f"Profiles saved:      {result.get('profiles_saved', 0)}"
    )
    print(
        f"Errors:              {result.get('errors_count', 0)}"
    )
    print(f"Typed profiles:      {stats.get('typed', 0)}")
    print(f"Unknown type:        {stats.get('unknown_type', 0)}")
    print(f"With entity:         {stats.get('with_entity', 0)}")

    print("\nProfiles by type:")

    for product_type, count in (stats.get("by_type") or {}).items():
        print(f"  {product_type}: {count}")

    errors = result.get("errors") or []

    if errors:
        print("\nErrors:")

        for error in errors:
            print(
                f"- {error.get('title')} "
                f"{error.get('url')}: "
                f"{error.get('error')}"
            )


if __name__ == "__main__":
    print_summary(sync_repository_catalog_intelligence())
