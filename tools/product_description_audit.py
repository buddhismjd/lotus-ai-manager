from __future__ import annotations

from dataclasses import dataclass

from backend.catalog.product_features import extract_product_features
from backend.catalog.product_intelligence import analyze_product
from backend.catalog.repositories import ProductRepository


MIN_DESCRIPTION_LENGTH = 80

RECOMMENDED_FIELDS: dict[str, tuple[str, ...]] = {
    "statue": (
        "высота и другие размеры",
        "материал",
        "страна и мастер изготовления",
        "изображённый аспект",
        "назначение: алтарь, практика или подарок",
        "возможность наполнения и благословения",
    ),
    "vajra": (
        "количество концов",
        "длина и вес",
        "материал",
        "происхождение",
        "назначение в практике",
    ),
    "amulet": (
        "изображённый аспект или символ",
        "материал и размер",
        "назначение и защитные свойства",
        "способ ношения",
        "происхождение",
    ),
    "mala": (
        "количество бусин",
        "материал бусин",
        "размер бусин и общая длина",
        "назначение в практике",
        "происхождение",
    ),
    "incense": (
        "состав",
        "аромат",
        "страна производства",
        "количество палочек или вес",
        "назначение",
    ),
    "jewelry": (
        "материал",
        "размер",
        "камни и символы",
        "вес",
        "страна изготовления",
    ),
    "ritual_item": (
        "точное назначение",
        "материал",
        "размер",
        "традиция использования",
        "происхождение",
    ),
    "thangka": (
        "изображённый аспект",
        "размер полотна",
        "техника и материалы",
        "автор или школа",
        "происхождение",
    ),
    "singing_bowl": (
        "диаметр и высота",
        "вес",
        "материал и состав сплава",
        "тональность",
        "наличие палочки и подушки",
    ),
}


@dataclass(frozen=True, slots=True)
class DescriptionRecommendation:
    title: str
    url: str
    product_type: str | None
    reasons: tuple[str, ...]
    recommended_fields: tuple[str, ...]


def audit_product(product) -> DescriptionRecommendation | None:
    title = product.title or ""
    description = product.description or ""
    category = getattr(product, "category", "") or ""
    sku = getattr(product, "sku", "") or ""

    intelligence = analyze_product(
        title=title,
        description=description,
        category=category,
        sku=sku,
    )
    features = extract_product_features(
        " ".join([title, description, category])
    )

    reasons: list[str] = []

    if not description.strip():
        reasons.append("описание отсутствует")
    elif len(description.strip()) < MIN_DESCRIPTION_LENGTH:
        reasons.append("описание слишком короткое")

    if intelligence.product_type in {"statue", "vajra", "singing_bowl"}:
        if not features.dimensions_cm:
            reasons.append("не указан размер")

    if intelligence.product_type == "vajra" and not features.point_counts:
        reasons.append("не указано количество концов")

    if not reasons:
        return None

    return DescriptionRecommendation(
        title=title,
        url=product.url,
        product_type=intelligence.product_type,
        reasons=tuple(reasons),
        recommended_fields=RECOMMENDED_FIELDS.get(
            intelligence.product_type or "",
            (
                "размер",
                "материал",
                "происхождение",
                "назначение",
            ),
        ),
    )


def build_description_recommendations() -> list[DescriptionRecommendation]:
    recommendations = [
        recommendation
        for product in ProductRepository().list_all()
        if (recommendation := audit_product(product)) is not None
    ]

    return sorted(
        recommendations,
        key=lambda item: (
            item.product_type or "zz",
            item.title.lower(),
        ),
    )


def main() -> None:
    recommendations = build_description_recommendations()

    print("=" * 72)
    print("AI BODHI PRODUCT DESCRIPTION RECOMMENDATIONS")
    print("=" * 72)
    print(f"Товаров с рекомендациями: {len(recommendations)}")

    for item in recommendations:
        print(f"\n- {item.title}")
        print(f"  Тип: {item.product_type or 'unknown'}")
        print(f"  Причины: {', '.join(item.reasons)}")
        print(
            "  Рекомендуется добавить: "
            + "; ".join(item.recommended_fields)
        )
        print(f"  URL: {item.url}")


if __name__ == "__main__":
    main()
