from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from backend.catalog.product_profiles import (
    ProductProfile,
    get_product_profile,
)
from backend.catalog.repositories import ProductRepository


PRODUCT_UID_RE = re.compile(
    r"/tproduct/(?P<uid>\d+)",
    re.IGNORECASE,
)

PRODUCT_TYPE_LABELS = {
    "statue": "Статуи",
    "thangka": "Тханки",
    "amulet": "Амулеты",
    "mala": "Малы (чётки)",
    "vajra": "Ваджры",
    "incense": "Благовония",
    "jewelry": "Украшения",
    "ritual_item": "Ритуальные предметы",
    "singing_bowl": "Поющие чаши",
    "bowl": "Поющие чаши",
    "unknown": "Другое",
}


def normalize_aspect(value: str | None) -> str:
    text = (value or "").lower().replace("ё", "е")
    text = re.sub(r"[^a-zа-я0-9\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True, slots=True)
class AspectProduct:
    title: str
    url: str
    product_type: str
    product_type_label: str


@dataclass(frozen=True, slots=True)
class AspectGroup:
    aspect: str
    products: tuple[AspectProduct, ...]

    @property
    def by_type(self) -> dict[str, tuple[AspectProduct, ...]]:
        grouped: dict[str, list[AspectProduct]] = {}

        for product in self.products:
            grouped.setdefault(
                product.product_type_label,
                [],
            ).append(product)

        return {
            label: tuple(items)
            for label, items in grouped.items()
        }

    def summary_lines(self) -> tuple[str, ...]:
        lines = [f"Аспект: {self.aspect}"]

        for label, products in self.by_type.items():
            lines.append(
                f"{label}: {len(products)}"
            )

        return tuple(lines)


def _profile_id_from_product(product) -> str | None:
    url = str(getattr(product, "url", "") or "")
    match = PRODUCT_UID_RE.search(url)

    if match:
        return f"product-{match.group('uid')}"

    source_id = str(
        getattr(product, "source_id", "")
        or getattr(product, "id", "")
        or ""
    ).strip()

    if not source_id:
        return None

    if source_id.startswith("product-"):
        return source_id

    return f"product-{source_id}"


def _profile_aspects(profile: ProductProfile) -> tuple[str, ...]:
    aspects = getattr(profile, "aspects", None)

    if aspects is not None:
        return tuple(aspects)

    # Backward compatibility with the existing DB/model field.
    return tuple(profile.entities)


def build_aspect_index() -> dict[str, AspectGroup]:
    buckets: dict[
        str,
        dict[str, object],
    ] = {}

    for product in ProductRepository().list_all():
        profile_id = _profile_id_from_product(product)

        if not profile_id:
            continue

        profile = get_product_profile(profile_id)

        if profile is None:
            continue

        aspects = _profile_aspects(profile)

        if not aspects:
            continue

        product_type = profile.product_type or "unknown"
        product_item = AspectProduct(
            title=product.title or "",
            url=product.url or "",
            product_type=product_type,
            product_type_label=PRODUCT_TYPE_LABELS.get(
                product_type,
                product_type,
            ),
        )

        for aspect in aspects:
            normalized = normalize_aspect(aspect)

            if not normalized:
                continue

            bucket = buckets.setdefault(
                normalized,
                {
                    "aspect": aspect,
                    "products": {},
                },
            )
            products = bucket["products"]
            products[product_item.url] = product_item

    return {
        normalized: AspectGroup(
            aspect=str(bucket["aspect"]),
            products=tuple(
                sorted(
                    bucket["products"].values(),
                    key=lambda item: (
                        item.product_type_label,
                        item.title.lower(),
                        item.url,
                    ),
                )
            ),
        )
        for normalized, bucket in buckets.items()
    }


def find_aspect_group(
    aspect: str,
    *,
    index: dict[str, AspectGroup] | None = None,
) -> AspectGroup | None:
    index = index or build_aspect_index()
    normalized = normalize_aspect(aspect)

    if normalized in index:
        return index[normalized]

    # Inflection-friendly fallback:
    # Дзамбала / Дзамбалы / Дзамбале.
    stem = normalized[: max(4, len(normalized) - 2)]

    candidates = [
        group
        for key, group in index.items()
        if key.startswith(stem) or normalized.startswith(
            key[: max(4, len(key) - 2)]
        )
    ]

    if len(candidates) == 1:
        return candidates[0]

    return None


def format_aspect_response(
    group: AspectGroup,
    *,
    max_items_per_type: int = 3,
) -> str:
    lines = [
        f"По аспекту «{group.aspect}» "
        "в магазине есть разные виды товаров:"
    ]

    for label, products in group.by_type.items():
        lines.append(f"\n{label} — {len(products)}")

        for product in products[:max_items_per_type]:
            lines.append(
                f"• {product.title}\n  {product.url}"
            )

        remaining = len(products) - max_items_per_type

        if remaining > 0:
            lines.append(
                f"• Ещё вариантов: {remaining}"
            )

    lines.append(
        "\nУточните, какой вид товара Вас интересует."
    )
    return "\n".join(lines)


def list_aspect_groups() -> list[AspectGroup]:
    return sorted(
        build_aspect_index().values(),
        key=lambda group: group.aspect.lower(),
    )


__all__ = [
    "AspectGroup",
    "AspectProduct",
    "build_aspect_index",
    "find_aspect_group",
    "format_aspect_response",
    "list_aspect_groups",
    "normalize_aspect",
]
