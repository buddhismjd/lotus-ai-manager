from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ResponseKind = Literal["product", "tour", "fallback"]


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


def build_product_response(
    title: str,
    summary: str = "",
    url: str = "",
) -> BuiltResponse:
    """Build a warm, factual response for one product."""
    clean_title = _clean(title)
    clean_summary = _clean(summary)
    clean_url = _clean(url)

    if not clean_title:
        return build_fallback_response(
            "Сейчас я не смог определить название товара."
        )

    text = _join_blocks(
        "🌸 Да, у нас есть подходящий вариант.",
        f"**{clean_title}**",
        clean_summary,
        f"Подробнее:\n{clean_url}" if clean_url else "",
        (
            "Если хотите, я могу помочь найти похожие предметы "
            "или подобрать вариант под вашу задачу."
        ),
    )

    return BuiltResponse(
        kind="product",
        text=text,
        title=clean_title,
        url=clean_url or None,
    )


def build_tour_response(
    title: str,
    summary: str = "",
    url: str = "",
) -> BuiltResponse:
    """Build a warm, factual response for one tour."""
    clean_title = _clean(title)
    clean_summary = _clean(summary)
    clean_url = _clean(url)

    if not clean_title:
        return build_fallback_response(
            "Сейчас я не смог определить название путешествия."
        )

    text = _join_blocks(
        "🌸 Думаю, вам может подойти это путешествие.",
        f"**{clean_title}**",
        clean_summary,
        f"Подробнее:\n{clean_url}" if clean_url else "",
        (
            "Если хотите, я могу показать похожие маршруты "
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
    """Build an honest fallback when no reliable result is available."""
    clean_reason = _clean(reason)

    text = _join_blocks(
        clean_reason
        or "🌸 Сейчас я не смог найти достоверную информацию по вашему вопросу.",
        (
            "Попробуйте сформулировать запрос немного иначе. "
            "Я также могу помочь найти товар, путешествие "
            "или связаться со специалистом."
        ),
    )

    return BuiltResponse(kind="fallback", text=text)


__all__ = [
    "BuiltResponse",
    "build_product_response",
    "build_tour_response",
    "build_fallback_response",
]
