from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Literal

from backend.catalog.repositories import ProductRepository, TourRepository


Intent = Literal[
    "tour",
    "product",
    "psychologist",
    "contacts",
    "reviews",
    "general",
    "unknown",
]


PSYCHOLOGIST_WORDS = {
    "психолог",
    "консультация",
    "буддолог",
    "стресс",
    "эмоции",
    "осознанность",
    "терапия",
}

CONTACT_WORDS = {
    "контакты",
    "телефон",
    "почта",
    "email",
    "адрес",
    "связаться",
}

REVIEWS_WORDS = {
    "отзывы",
    "отзыв",
    "мнения клиентов",
}

TOUR_GENERIC_WORDS = {
    "тур",
    "туры",
    "поездка",
    "путешествие",
    "ретрит",
    "паломничество",
    "маршрут",
}

PRODUCT_GENERIC_WORDS = {
    "товар",
    "магазин",
    "купить",
    "заказать",
    "цена",
    "стоимость",
    "наличие",
    "продаете",
    "продаёте",
}

STORE_PATTERNS = (
    re.compile(r"\bу\s+вас\s+.+\s+есть\b", re.IGNORECASE),
    re.compile(r"\bесть\s+ли\s+у\s+вас\b", re.IGNORECASE),
    re.compile(r"\bможно\s+ли\s+купить\b", re.IGNORECASE),
    re.compile(
        r"\bмне\s+(?:нужен|нужна|нужно|нужны)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:есть|в наличии|продается|продаётся)\??$",
        re.IGNORECASE,
    ),
)

STOPWORDS = {
    "есть",
    "ли",
    "у",
    "вас",
    "мне",
    "нужен",
    "нужна",
    "нужно",
    "нужны",
    "хочу",
    "купить",
    "покажите",
    "покажи",
    "товар",
    "около",
    "примерно",
    "какой",
    "какая",
    "какие",
    "это",
}


@dataclass(frozen=True)
class Route:
    intent: Intent
    confidence: float
    reason: str
    matched_title: str | None = None
    matched_url: str | None = None


def normalize(text: str) -> str:
    value = (text or "").lower().replace("ё", "е")
    value = re.sub(r"[^a-zа-я0-9\s-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def tokens(text: str) -> list[str]:
    return [
        word
        for word in re.findall(
            r"[a-zа-я0-9]{3,}",
            normalize(text),
        )
        if word not in STOPWORDS
    ]


def stem(word: str) -> str:
    word = normalize(word)

    endings = (
        "иями",
        "ями",
        "ами",
        "ого",
        "ему",
        "ыми",
        "ими",
        "ией",
        "иям",
        "иях",
        "ов",
        "ев",
        "ей",
        "ам",
        "ям",
        "ах",
        "ях",
        "ую",
        "юю",
        "ая",
        "яя",
        "ое",
        "ее",
        "ые",
        "ие",
        "ый",
        "ий",
        "ой",
        "а",
        "я",
        "ы",
        "и",
        "у",
        "ю",
        "е",
        "о",
    )

    for ending in endings:
        if word.endswith(ending) and len(word) - len(ending) >= 4:
            return word[: -len(ending)]

    return word


def contains_any(text: str, words: set[str]) -> bool:
    normalized = normalize(text)
    return any(normalize(word) in normalized for word in words)


def _contains_token_phrase(
    phrase_tokens: list[str],
    target_tokens: list[str],
) -> bool:
    if not phrase_tokens or len(phrase_tokens) > len(target_tokens):
        return False

    width = len(phrase_tokens)
    return any(
        target_tokens[index : index + width] == phrase_tokens
        for index in range(len(target_tokens) - width + 1)
    )


def _fuzzy_ratio(left: str, right: str) -> float:
    left_stem = stem(left)
    right_stem = stem(right)

    if not left_stem or not right_stem:
        return 0.0

    if left_stem != right_stem and (
        left_stem in right_stem or right_stem in left_stem
    ):
        return 0.0

    return SequenceMatcher(None, left_stem, right_stem).ratio()


def _index_item(
    title: str,
    url: str,
    searchable_parts: list[str | None],
) -> dict:
    searchable = " ".join(
        part.strip()
        for part in searchable_parts
        if part and part.strip()
    )

    title_tokens = tokens(title)
    search_tokens = tokens(searchable)

    return {
        "title": title,
        "url": url,
        "normalized": normalize(searchable),
        "title_tokens": title_tokens,
        "search_tokens": search_tokens,
        "title_stems": {stem(word) for word in title_tokens},
        "search_stems": {stem(word) for word in search_tokens},
    }


@lru_cache(maxsize=1)
def catalog_index() -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {
        "product": [],
        "tour": [],
    }

    for product in ProductRepository().list_all():
        index["product"].append(
            _index_item(
                title=product.title,
                url=product.url,
                searchable_parts=[
                    product.title,
                    product.category,
                    product.description,
                    product.material,
                    " ".join(product.keywords),
                ],
            )
        )

    for tour in TourRepository().list_all():
        index["tour"].append(
            _index_item(
                title=tour.title,
                url=tour.url,
                searchable_parts=[
                    tour.title,
                    tour.country,
                    tour.region,
                    tour.description,
                    tour.difficulty,
                    tour.guide,
                    " ".join(tour.keywords),
                ],
            )
        )

    return index


def reload_catalog_index() -> None:
    catalog_index.cache_clear()


def best_catalog_match(
    query: str,
    page_type: str,
) -> tuple[float, dict | None]:
    query_tokens = tokens(query)
    query_stems = {stem(word) for word in query_tokens}

    if not query_tokens:
        return 0.0, None

    best_score = 0.0
    best_item = None

    for item in catalog_index().get(page_type, []):
        score = 0.0

        title_stems = item["title_stems"]
        search_stems = item["search_stems"]

        exact_title_hits = len(query_stems & title_stems)
        search_hits = len(query_stems & search_stems)

        score += exact_title_hits * 35
        score += max(0, search_hits - exact_title_hits) * 8

        title_tokens = item["title_tokens"]

        if _contains_token_phrase(query_tokens, title_tokens):
            score += 70

        if _contains_token_phrase(title_tokens, query_tokens):
            score += 70

        for query_word in query_tokens:
            for title_word in title_tokens:
                ratio = _fuzzy_ratio(query_word, title_word)

                if ratio >= 0.88:
                    score += 25
                elif ratio >= 0.78:
                    score += 10

        if score > best_score:
            best_score = score
            best_item = item

    return best_score, best_item


def looks_like_store_request(text: str) -> bool:
    normalized = normalize(text)

    if contains_any(normalized, PRODUCT_GENERIC_WORDS):
        return True

    return any(
        pattern.search(normalized)
        for pattern in STORE_PATTERNS
    )


def route_query(text: str) -> Route:
    normalized = normalize(text)

    if not normalized:
        return Route("unknown", 1.0, "empty")

    if contains_any(normalized, PSYCHOLOGIST_WORDS):
        return Route(
            "psychologist",
            0.98,
            "psychologist_marker",
        )

    if contains_any(normalized, CONTACT_WORDS):
        return Route(
            "contacts",
            0.95,
            "contact_marker",
        )

    if contains_any(normalized, REVIEWS_WORDS):
        return Route(
            "reviews",
            0.95,
            "reviews_marker",
        )

    product_score, product = best_catalog_match(
        normalized,
        "product",
    )
    tour_score, tour = best_catalog_match(
        normalized,
        "tour",
    )

    store_context = looks_like_store_request(normalized)
    tour_context = contains_any(
        normalized,
        TOUR_GENERIC_WORDS,
    )

    if product and product_score >= 30:
        if product_score >= tour_score or store_context:
            return Route(
                "product",
                min(0.99, 0.65 + product_score / 200),
                "dynamic_product_match",
                product["title"],
                product["url"],
            )

    if tour and tour_score >= 30:
        if tour_score > product_score or tour_context:
            return Route(
                "tour",
                min(0.99, 0.65 + tour_score / 200),
                "dynamic_tour_match",
                tour["title"],
                tour["url"],
            )

    if tour_context:
        return Route(
            "tour",
            0.88,
            "generic_tour_request",
        )

    if store_context:
        return Route(
            "product",
            0.82,
            "store_request_without_match",
        )

    return Route(
        "unknown",
        0.25,
        "no_safe_route",
    )


if __name__ == "__main__":
    import sys

    query = (
        " ".join(sys.argv[1:]).strip()
        or "У вас Тяньши есть?"
    )
    result = route_query(query)

    print(f"Query: {query}")
    print(f"Intent: {result.intent}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Reason: {result.reason}")
    print(f"Matched: {result.matched_title or '-'}")
    print(f"URL: {result.matched_url or '-'}")
