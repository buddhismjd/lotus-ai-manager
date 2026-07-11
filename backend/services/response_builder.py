from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


ResponseKind = Literal["product", "tour", "fallback"]

DESCRIPTION_RECOMMENDATIONS: dict[str, tuple[str, ...]] = {
    "statue": (
        "высоту и другие размеры",
        "материал",
        "страну и мастера изготовления",
        "изображённый аспект",
        "назначение: алтарь, практика или подарок",
    ),
    "thangka": (
        "изображённый аспект",
        "размер полотна",
        "технику и материалы",
        "автора или школу",
        "происхождение",
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
        "материал и размер бусин",
        "общую длину",
        "назначение в практике",
        "происхождение",
    ),
    "vajra": (
        "количество концов",
        "длину и вес",
        "материал",
        "происхождение",
        "назначение в практике",
    ),
    "incense": (
        "состав",
        "аромат",
        "страну производства",
        "количество или вес",
        "назначение",
    ),
    "jewelry": (
        "материал",
        "размер",
        "камни и символы",
        "вес",
        "страну изготовления",
    ),
    "ritual_item": (
        "точное назначение",
        "материал",
        "размер",
        "традицию использования",
        "происхождение",
    ),
    "singing_bowl": (
        "диаметр и высоту",
        "вес",
        "материал и состав сплава",
        "тональность",
        "комплектацию",
    ),
}


@dataclass(frozen=True, slots=True)
class BuiltResponse:
    """Final user-facing response produced by AI Bodhi."""

    kind: ResponseKind
    text: str
    title: str | None = None
    url: str | None = None


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _join_blocks(*blocks: str) -> str:
    return "\n\n".join(block for block in blocks if block)


def _description_recommendation_text(
    product_type: str | None,
) -> str:
    fields = DESCRIPTION_RECOMMENDATIONS.get(
        product_type or "",
        (
            "размер",
            "материал",
            "происхождение",
            "назначение",
        ),
    )

    return (
        "В карточке пока нет подробного описания. "
        "Чтобы я мог точнее консультировать покупателей, "
        "в будущем стоит добавить: "
        + "; ".join(fields)
        + "."
    )


def build_product_response(
    title: str,
    summary: str = "",
    url: str = "",
    *,
    product_type: str | None = None,
    note: str = "",
) -> BuiltResponse:
    """Build a warm, factual response for one product."""
    clean_title = _clean(title)
    clean_summary = _clean(summary)
    clean_url = _clean(url)
    clean_note = _clean(note)

    if not clean_title:
        return build_fallback_response(
            "Сейчас я не смог определить название товара."
        )

    description_block = (
        clean_summary
        if clean_summary
        else _description_recommendation_text(product_type)
    )

    text = _join_blocks(
        "🌸 Да, у нас есть подходящий вариант.",
        f"**{clean_title}**",
        description_block,
        clean_note,
        f"Подробнее:\n{clean_url}" if clean_url else "",
        (
            "Я могу показать другие варианты этого аспекта "
            "или подобрать предмет по размеру, материалу и назначению."
        ),
    )

    return BuiltResponse(
        kind="product",
        text=text,
        title=clean_title,
        url=clean_url or None,
    )


def build_aspect_response(
    aspect: str,
    grouped_products: Sequence[
        tuple[str, Sequence[tuple[str, str]]]
    ],
) -> BuiltResponse:
    """
    Build a grouped answer for a general aspect query.

    grouped_products:
        (
            ("Статуи", (("Статуя Дзамбалы", "https://..."), ...)),
            ("Амулеты", (...)),
        )
    """
    clean_aspect = _clean(aspect)

    if not clean_aspect or not grouped_products:
        return build_fallback_response(
            "По этому аспекту пока не удалось найти товары."
        )

    lines = [
        f"🌸 По аспекту **«{clean_aspect}»** "
        "в магазине представлены разные виды товаров:"
    ]

    first_title: str | None = None
    first_url: str | None = None

    for label, products in grouped_products:
        products = tuple(products)

        if not products:
            continue

        lines.append(f"\n**{label} — {len(products)}**")

        for title, url in products[:3]:
            if first_title is None:
                first_title = title
                first_url = url

            lines.append(f"• {title}")
            if url:
                lines.append(f"  {url}")

        remaining = len(products) - 3
        if remaining > 0:
            lines.append(f"• Ещё вариантов: {remaining}")

    lines.append(
        "\nУточните, какой вид товара Вас интересует: "
        "статуя, амулет, тханка или другой предмет."
    )

    return BuiltResponse(
        kind="product",
        text="\n".join(lines),
        title=first_title,
        url=first_url,
    )


def build_tour_response(
    title: str,
    summary: str = "",
    url: str = "",
) -> BuiltResponse:
    clean_title = _clean(title)
    clean_summary = _clean(summary)
    clean_url = _clean(url)

    if not clean_title:
        return build_fallback_response(
            "Сейчас я не смог определить название путешествия."
        )

    text = _join_blocks(
        "🌸 Думаю, Вам может подойти это путешествие.",
        f"**{clean_title}**",
        clean_summary,
        f"Подробнее:\n{clean_url}" if clean_url else "",
        (
            "Я могу показать похожие маршруты "
            "или помочь уточнить даты и программу."
        ),
    )

    return BuiltResponse(
        kind="tour",
        text=text,
        title=clean_title,
        url=clean_url or None,
    )


def build_fallback_response(reason: str = "") -> BuiltResponse:
    clean_reason = _clean(reason)

    text = _join_blocks(
        clean_reason
        or (
            "🌸 Сейчас я не смог найти достоверную "
            "информацию по Вашему вопросу."
        ),
        (
            "Попробуйте сформулировать запрос немного иначе. "
            "Я также могу помочь найти товар, путешествие "
            "или связаться со специалистом."
        ),
    )

    return BuiltResponse(kind="fallback", text=text)


__all__ = [
    "BuiltResponse",
    "build_aspect_response",
    "build_product_response",
    "build_tour_response",
    "build_fallback_response",
]
