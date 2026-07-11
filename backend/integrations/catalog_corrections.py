from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Any

from backend.catalog.product_profiles import (
    ProductProfile,
    get_product_profile,
    save_product_profile,
)
from backend.catalog.repositories import ProductRepository
from backend.storage.database import save_document


VAJRA_ID = "product-296122659532"
VAJRA_URL = (
    "https://svet-lotosa.tilda.ws/"
    "tproduct/296122659532-vadzhra"
)
VAJRA_TITLE = "Ваджра"
VAJRA_DESCRIPTION = (
    "Ритуальный предмет Ваджра. "
    "Символ духовной силы, практики и защиты."
)

PROTECTIVE_AMULET_TITLE_FRAGMENT = "Пхурба Дордже"


def _unique(values: tuple[str, ...], *extra: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            value
            for value in [*values, *extra]
            if value and value.strip()
        )
    )


def upsert_vajra() -> None:
    content = "\n".join(
        [
            VAJRA_TITLE,
            VAJRA_DESCRIPTION,
            "Тип товара: vajra",
            "Назначение: practice, protection",
            "Синонимы: дордже, vajra, ритуальный предмет",
        ]
    )

    save_document(
        {
            "id": VAJRA_ID,
            "source_type": "catalog_correction",
            "type": "product",
            "title": VAJRA_TITLE,
            "url": VAJRA_URL,
            "summary": VAJRA_DESCRIPTION,
            "content": content,
            "enabled": True,
            "priority": 250,
            "content_hash": hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest(),
            "chunks": [content],
        }
    )

    save_product_profile(
        ProductProfile(
            product_id=VAJRA_ID,
            product_type="vajra",
            materials=(),
            usages=("practice", "protection"),
            traditions=("Ваджраяна",),
            synonyms=(
                "ваджра",
                "дордже",
                "vajra",
                "ритуальный предмет",
            ),
            keywords=(
                "ваджра",
                "дордже",
                "vajra",
                "ритуал",
                "практика",
                "защита",
            ),
            source_hash=hashlib.sha256(
                VAJRA_URL.encode("utf-8")
            ).hexdigest(),
        )
    )


def enrich_protective_amulet() -> bool:
    products = ProductRepository().list_all()

    product = next(
        (
            item
            for item in products
            if PROTECTIVE_AMULET_TITLE_FRAGMENT.lower()
            in (item.title or "").lower()
        ),
        None,
    )

    if product is None:
        return False

    import re

    match = re.search(r"/tproduct/(\d+)", product.url or "")

    if not match:
        return False

    profile_id = f"product-{match.group(1)}"
    profile = get_product_profile(profile_id)

    if profile is None:
        profile = ProductProfile(
            product_id=profile_id,
            product_type="amulet",
        )

    updated = replace(
        profile,
        product_type="amulet",
        usages=_unique(profile.usages, "protection", "practice"),
        synonyms=_unique(
            profile.synonyms,
            "защитный амулет",
            "оберег",
            "пхурба",
        ),
        keywords=_unique(
            profile.keywords,
            "защита",
            "защитный амулет",
            "пхурба",
            "дордже",
        ),
    )
    save_product_profile(updated)
    return True


def apply_catalog_corrections() -> dict[str, Any]:
    upsert_vajra()
    protective_amulet_updated = enrich_protective_amulet()

    return {
        "vajra_upserted": True,
        "protective_amulet_updated": protective_amulet_updated,
    }


def print_summary(result: dict[str, Any]) -> None:
    print("=" * 72)
    print("AI BODHI CATALOG CORRECTIONS")
    print("=" * 72)
    print(f"Vajra upserted:             {result['vajra_upserted']}")
    print(
        "Protective amulet updated: "
        f"{result['protective_amulet_updated']}"
    )


if __name__ == "__main__":
    print_summary(apply_catalog_corrections())
