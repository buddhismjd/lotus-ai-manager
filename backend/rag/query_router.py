from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


Intent = Literal[
    "tour",
    "product",
    "psychologist",
    "contacts",
    "reviews",
    "general",
    "unknown",
]


TOUR_WORDS = {
    "тур", "туры", "поездка", "путешествие", "ретрит", "паломничество",
    "кайлас", "лапчи", "тибет", "непал", "бутан", "индия", "алтай",
    "монголия", "ладакх", "занскар", "куллу", "белуха", "марха",
}

PRODUCT_WORDS = {
    "товар", "магазин", "купить", "заказать", "цена", "стоимость",
    "статуя", "статуи", "ваджра", "дордже", "четки", "чётки",
    "серьги", "подвеска", "подвески", "гау", "благовония",
    "колокольчик", "танка", "ритуальный", "будда", "тара",
}

PSYCHOLOGIST_WORDS = {
    "психолог", "консультация", "буддолог", "стресс", "эмоции",
    "осознанность", "терапия", "записаться на консультацию",
}

CONTACT_WORDS = {
    "контакты", "телефон", "почта", "email", "адрес", "связаться",
}

REVIEWS_WORDS = {
    "отзывы", "отзыв", "мнения клиентов",
}

GENERAL_ALLOWED_WORDS = {
    "свет лотоса", "о студии", "кто вы", "чем занимаетесь",
}

STORE_AVAILABILITY_PATTERNS = (
    re.compile(r"\bу\s+вас\s+.+\s+есть\b", re.IGNORECASE),
    re.compile(r"\bесть\s+ли\s+у\s+вас\b", re.IGNORECASE),
    re.compile(r"\bможно\s+ли\s+купить\b", re.IGNORECASE),
    re.compile(r"\bмне\s+(?:нужен|нужна|нужно|нужны)\b", re.IGNORECASE),
    re.compile(r"\bищу\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class Route:
    intent: Intent
    confidence: float
    reason: str


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        (text or "").lower().replace("ё", "е"),
    ).strip()


def contains_any(text: str, words: set[str]) -> bool:
    normalized = normalize(text)
    return any(normalize(word) in normalized for word in words)


def looks_like_store_availability(text: str) -> bool:
    normalized = normalize(text)

    if any(pattern.search(normalized) for pattern in STORE_AVAILABILITY_PATTERNS):
        return True

    # Короткие запросы с существительным и вопросом о наличии:
    # «Гаплинг есть?», «Ваджра в наличии?»
    if re.search(r"\b(?:есть|в наличии|продается|продаёте)\b", normalized):
        if not contains_any(normalized, TOUR_WORDS | PSYCHOLOGIST_WORDS):
            return True

    return False


def route_query(text: str) -> Route:
    normalized = normalize(text)

    if not normalized:
        return Route("unknown", 1.0, "empty")

    if contains_any(normalized, PSYCHOLOGIST_WORDS):
        return Route("psychologist", 0.98, "psychologist_marker")

    if contains_any(normalized, TOUR_WORDS):
        return Route("tour", 0.96, "tour_marker")

    if contains_any(normalized, PRODUCT_WORDS):
        return Route("product", 0.98, "product_marker")

    if looks_like_store_availability(normalized):
        return Route(
            "product",
            0.82,
            "store_availability_pattern",
        )

    if contains_any(normalized, CONTACT_WORDS):
        return Route("contacts", 0.95, "contact_marker")

    if contains_any(normalized, REVIEWS_WORDS):
        return Route("reviews", 0.95, "reviews_marker")

    if contains_any(normalized, GENERAL_ALLOWED_WORDS):
        return Route("general", 0.75, "allowed_general_marker")

    return Route("unknown", 0.25, "no_safe_route")


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]).strip() or "У вас Гаплинг есть?"
    result = route_query(query)

    print(f"Query: {query}")
    print(f"Intent: {result.intent}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Reason: {result.reason}")
