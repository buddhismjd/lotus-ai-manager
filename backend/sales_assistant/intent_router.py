from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from backend.sales_assistant.strategy import detect_month
from backend.sales_assistant.tour_discovery import understand_tour_query

CommercialIntent = Literal["tour", "product", "psychologist", "contacts", "unknown"]


@dataclass(frozen=True, slots=True)
class IntentDecision:
    primary: CommercialIntent
    confidence: float
    signals: tuple[str, ...] = ()
    is_catalog_query: bool = False
    label: str | None = None


_TOUR_MARKERS = (
    "тур", "поездк", "путешеств", "паломнич", "ретрит", "кора",
    "хочу поехать", "хочу в", "отправиться", "возите",
)
_PRODUCT_MARKERS = (
    "товар", "купить", "магазин", "в наличии", "под заказ", "цена",
    "стату", "тханк", "танк", "чаш", "ваджр", "пхурб", "четк",
    "чётк", "благовон", "кулон", "подвес", "амулет", "наклей",
)
_SERVICE_MARKERS = (
    "психолог", "буддолог", "консультац", "записаться", "терап",
)
_CONTACT_MARKERS = (
    "контакт", "телефон", "написать менеджеру", "связаться", "whatsapp",
    "telegram", "телеграм", "ватсап",
)
_CATALOG_MARKERS = (
    "покажи", "покажите", "что есть", "что по", "какие тур", "найди", "найдите",
    "туры в", "поездки в", "путешествия в", "возите",
    "хочу в", "хочу поехать",
)


def _normalise(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


def _contains_any(text: str, markers: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(marker for marker in markers if marker in text)


def classify_commercial_intent(query: str) -> IntentDecision:
    """Choose the commercial catalogue before legacy page routing.

    The router uses structured tour vocabulary rather than a hard-coded rule
    for one country. Explicit product/service/contact language wins over a
    destination mention, while a bare destination is treated as a tour search.
    """
    text = _normalise(query)
    discovery = understand_tour_query(text)

    product_hits = _contains_any(text, _PRODUCT_MARKERS)
    service_hits = _contains_any(text, _SERVICE_MARKERS)
    contact_hits = _contains_any(text, _CONTACT_MARKERS)
    tour_hits = _contains_any(text, _TOUR_MARKERS)
    catalog_hits = _contains_any(text, _CATALOG_MARKERS)

    if service_hits:
        return IntentDecision("psychologist", 0.98, service_hits)
    if contact_hits:
        return IntentDecision("contacts", 0.96, contact_hits)
    if product_hits:
        return IntentDecision("product", 0.94, product_hits, is_catalog_query=True)

    destination_signals = (
        discovery.destinations + discovery.directions + discovery.aspects
    )
    time_signal = bool(discovery.natural_periods or detect_month(text) is not None)
    if destination_signals or tour_hits or time_signal:
        label = next(iter(destination_signals), None)
        confidence = 0.97 if destination_signals else 0.88
        bare_destination = bool(
            label and text == _normalise(label)
        )
        return IntentDecision(
            "tour",
            confidence,
            tuple(destination_signals) + tour_hits,
            is_catalog_query=bool(
                destination_signals and (bare_destination or catalog_hits)
            ),
            label=label,
        )

    return IntentDecision("unknown", 0.0)


__all__ = ["CommercialIntent", "IntentDecision", "classify_commercial_intent"]
