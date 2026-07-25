from __future__ import annotations

import re
from dataclasses import replace
from decimal import Decimal
from typing import Iterable

from backend.catalog.models import Product, Tour
from backend.catalog.repositories import ProductRepository, TourRepository
from backend.services.response_builder import BuiltResponse

_NAVIGATION_LINES = {
    "путешествия",
    "магазин",
    "психолог-буддолог",
    "отзывы",
    "связаться с нами",
}
_CTA_LINES = {
    "отправить заявку",
    "оставить заявку",
    "купить",
    "заказать",
    "подробнее",
}
_ROUTE_MARKERS = (
    "план маршрута",
    "программа тура",
    "программа путешествия",
)
_DATE_RE = re.compile(
    r"\b\d{1,2}\s+"
    r"(?:января|февраля|марта|апреля|мая|июня|июля|августа|"
    r"сентября|октября|ноября|декабря)"
    r"\s*[–—-]\s*\d{1,2}\s+"
    r"(?:января|февраля|марта|апреля|мая|июня|июля|августа|"
    r"сентября|октября|ноября|декабря)\b",
    re.IGNORECASE,
)
_DURATION_RE = re.compile(r"\b(?P<days>\d{1,3})\s*(?:дней|дня|день)\b", re.IGNORECASE)
_DAY_LINE_RE = re.compile(r"^(?:🗓️\s*)?день\s*\d+\b", re.IGNORECASE)
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def _normalise_line(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split()).strip()


def _plain_text(value: str) -> str:
    return value.replace("**", "").replace("__", "").strip()


def _source_lines(value: str) -> list[str]:
    return [line for raw in value.splitlines() if (line := _normalise_line(raw))]


def _is_noise(line: str, *, title: str = "") -> bool:
    lowered = line.casefold().strip(" :")
    if lowered in _NAVIGATION_LINES or lowered in _CTA_LINES:
        return True
    if title:
        normal_title = _normalise_line(title).casefold()
        if lowered == normal_title:
            return True
        title_lead = re.split(r"\s*[–—-]\s*", normal_title, maxsplit=1)[0].strip()
        if title_lead and lowered.startswith(title_lead) and _DURATION_RE.search(line):
            return True
    if _URL_RE.fullmatch(line):
        return True
    return False


def _extract_date(lines: Iterable[str]) -> str | None:
    for line in lines:
        match = _DATE_RE.search(line)
        if match:
            return _normalise_line(match.group(0))
    return None


def _extract_duration(title: str, lines: Iterable[str], explicit: int | None) -> int | None:
    if explicit:
        return explicit
    for value in (title, *tuple(lines)):
        match = _DURATION_RE.search(value)
        if match:
            return int(match.group("days"))
    return None


def _short_summary(lines: Iterable[str], *, title: str, max_chars: int = 320) -> str:
    accepted: list[str] = []
    route_started = False

    for line in lines:
        lowered = line.casefold()
        if any(marker in lowered for marker in _ROUTE_MARKERS):
            route_started = True
            continue
        if route_started or _DAY_LINE_RE.match(line):
            continue
        if _is_noise(line, title=title) or _DATE_RE.fullmatch(line):
            continue
        if _DURATION_RE.fullmatch(line):
            continue
        accepted.append(line)
        if len(" ".join(accepted)) >= max_chars:
            break

    text = " ".join(accepted).strip()
    if len(text) <= max_chars:
        return text
    clipped = text[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:")
    return clipped + "…"


def _money(value: Decimal | None, currency: str) -> str | None:
    if value is None:
        return None
    amount = f"{value:,.0f}".replace(",", " ")
    symbols = {"RUR": "₽", "RUB": "₽", "USD": "$", "EUR": "€"}
    return f"{amount} {symbols.get(currency.upper(), currency)}".strip()


def _find_tour(response: BuiltResponse) -> Tour | None:
    for tour in TourRepository().list_all():
        if response.url and tour.url == response.url:
            return tour
        if response.title and tour.title == response.title:
            return tour
    return None


def _find_product(response: BuiltResponse) -> Product | None:
    for product in ProductRepository().list_all():
        if response.url and product.url == response.url:
            return product
        if response.title and product.title == response.title:
            return product
    return None


def _format_tour(response: BuiltResponse) -> BuiltResponse:
    tour = _find_tour(response)
    title = _plain_text(response.title or (tour.title if tour else ""))
    if not title:
        return replace(response, text=_plain_text(response.text))

    description = tour.description if tour else response.text
    lines = _source_lines(description)
    date_text = _extract_date(lines)
    summary = _short_summary(lines, title=title)
    url = response.url or (tour.url if tour else None)

    blocks = ["С радостью расскажу об этом путешествии.", f"🗻 {title}"]
    facts: list[str] = []
    if date_text:
        facts.append(f"📅 {date_text}")
    if tour and tour.country:
        facts.append(f"📍 {tour.country}")
    if tour:
        price = _money(tour.price, tour.currency)
        if price:
            prefix = "от " if tour.metadata.get("price_is_from") else ""
            facts.append(f"💳 {prefix}{price}")
    if facts:
        blocks.append("\n".join(facts))
    if summary:
        blocks.append(summary)
    blocks.append(
        "Если этот путь откликается Вам, я могу уточнить программу, стоимость или помочь сохранить интерес к поездке."
    )
    return replace(response, text="\n\n".join(blocks), title=title, url=url)


def _format_product(response: BuiltResponse) -> BuiltResponse:
    product = _find_product(response)
    title = _plain_text(response.title or (product.title if product else ""))
    if not title:
        return replace(response, text=_plain_text(response.text))

    description = product.description if product else response.text
    summary = _short_summary(_source_lines(description), title=title, max_chars=260)
    url = response.url or (product.url if product else None)

    blocks = ["С удовольствием покажу этот вариант.", f"🌸 {title}"]
    facts: list[str] = []
    if product:
        price = _money(product.price, product.currency)
        if price:
            facts.append(f"💳 {price}")
        stock = (product.availability_status or "").strip().casefold()
        if stock == "в наличии":
            facts.append("✅ В наличии")
        elif stock == "нет в наличии":
            facts.append("Нет в наличии")
        elif stock == "под заказ":
            facts.append("Под заказ")
        else:
            facts.append("⏳ Наличие уточняется")
        if product.material:
            facts.append(f"Материал: {product.material}")
    if facts:
        blocks.append("\n".join(facts))
    if summary:
        blocks.append(summary)
    blocks.append("Буду рада показать другие подходящие варианты или помочь с выбором.")
    return replace(response, text="\n\n".join(blocks), title=title, url=url)


def format_sales_response(response: BuiltResponse) -> BuiltResponse:
    """Convert repository output into a concise sales-oriented response."""
    if response.kind == "tour":
        return _format_tour(response)
    if response.kind == "product":
        return _format_product(response)
    return replace(response, text=_plain_text(response.text))


__all__ = ["format_sales_response"]

_MONTH_NAMES = {
    1: "январе",
    2: "феврале",
    3: "марте",
    4: "апреле",
    5: "мае",
    6: "июне",
    7: "июле",
    8: "августе",
    9: "сентябре",
    10: "октябре",
    11: "ноябре",
    12: "декабре",
}


def format_tour_list(
    tours: Iterable[Tour],
    month: int | None = None,
    limit: int | None = None,
) -> str:
    all_tours = list(tours)
    selected = all_tours if limit is None else all_tours[: max(1, limit)]
    if not selected:
        period = f" в {_MONTH_NAMES[month]}" if month in _MONTH_NAMES else ""
        return (
            f"К сожалению, я не нашёл опубликованных туров{period}. "
            "При желании могу сохранить Ваш интерес и передать его менеджеру."
        )

    period = f" в {_MONTH_NAMES[month]}" if month in _MONTH_NAMES else ""
    heading = f"Вот опубликованные туры{period}. С радостью покажу каждый вариант:"
    cards: list[str] = []

    for tour in selected:
        lines = _source_lines(tour.description)
        schedule = getattr(tour, "schedule", None)
        date_text = schedule.source_text if schedule else _extract_date(lines)
        card = [f"🗻 {tour.title}"]
        if date_text:
            card.append(f"📅 {date_text}")
        if tour.country:
            card.append(f"📍 {tour.country}")
        cards.append("\n".join(card))

    tail = "Могу подробнее рассказать о любом из этих путешествий или помочь выбрать подходящее."
    return "\n\n".join([heading, *cards, tail])


__all__ = ["format_sales_response", "format_tour_list"]
