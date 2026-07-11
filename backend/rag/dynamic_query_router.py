from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Literal

from backend.catalog.product_features import (
    dimension_distance,
    extract_product_features,
)
from backend.catalog.product_intelligence import analyze_product
from backend.catalog.product_profiles import get_product_profile
from backend.catalog.text_normalization import normalize_search_text
from backend.catalog.repositories import ProductRepository, TourRepository


PRODUCT_UID_RE = re.compile(
    r"/tproduct/(?P<uid>\d+)",
    re.IGNORECASE,
)


def _product_profile_id_from_url(url: str) -> str | None:
    match = PRODUCT_UID_RE.search(url or "")

    if not match:
        return None

    return f"product-{match.group('uid')}"


def _safe_get_product_profile(url: str):
    profile_id = _product_profile_id_from_url(url)

    if not profile_id:
        return None

    try:
        return get_product_profile(profile_id)
    except Exception:
        # Search remains available if profiles are not initialized yet.
        return None


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

PRODUCT_KIND_ALIASES = {
    "statue": {
        "статуя",
        "статуэтка",
        "скульптура",
        "фигура",
    },
    "amulet": {
        "амулет",
        "подвеска",
        "кулон",
        "медальон",
    },
    "mala": {
        "четки",
        "чётки",
        "мала",
    },
    "vajra": {
        "ваджра",
        "дордже",
    },
    "thangka": {
        "танка",
        "тханка",
    },
    "bowl": {
        "чаша",
        "поющая чаша",
    },
    "incense": {
        "благовоние",
        "благовония",
        "аромапалочки",
    },
}


PRODUCT_KIND_PREFIXES = {
    "statue": (
        "стату",
        "статуй",
        "скульптур",
        "фигур",
    ),
    "amulet": (
        "амулет",
        "подвес",
        "кулон",
        "медальон",
    ),
    "mala": (
        "четк",
        "чётк",
        "мала",
    ),
    "vajra": (
        "ваджр",
        "дордж",
    ),
    "thangka": (
        "танк",
        "тханк",
    ),
    "bowl": (
        "чаш",
    ),
    "incense": (
        "благовон",
        "аромапал",
    ),
}


PRODUCT_INTELLIGENCE_KIND_MAP = {
    "singing_bowl": "bowl",
}


def _canonical_product_kind(kind: str | None) -> str | None:
    if kind is None:
        return None

    return PRODUCT_INTELLIGENCE_KIND_MAP.get(kind, kind)


def analyze_query_semantics(text: str) -> dict[str, object]:
    intelligence = analyze_product(title=text)

    return {
        "product_kind": (
            _canonical_product_kind(intelligence.product_type)
            or detect_product_kind(text)
        ),
        "entities": {
            normalize(entity)
            for entity in intelligence.entities
        },
        "usages": set(intelligence.usages),
        "materials": {
            normalize(material)
            for material in intelligence.materials
        },
    }


def detect_product_kind(text: str) -> str | None:
    """
    Detect product type from stable lexical prefixes.

    Prefix matching is intentional: Russian case endings differ strongly
    (for example «статуя», «статую», «статуи», «статуй»), while the lexical
    base «стату-» remains stable.
    """
    for word in tokens(text):
        normalized_word = normalize(word)

        for kind, prefixes in PRODUCT_KIND_PREFIXES.items():
            if any(
                normalized_word.startswith(prefix)
                for prefix in prefixes
            ):
                return kind

    return None


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


QUERY_CORRECTIONS = {
    "кайлос": "кайлас",
    "каилас": "кайлас",
    "четкии": "четки",
    "стату": "статуя",
}

TOUR_CONTEXT_PREFIXES = (
    "тур",
    "поезд",
    "путешеств",
    "ретрит",
    "паломнич",
    "маршрут",
    "поход",
)

PRODUCT_CONTEXT_PREFIXES = tuple(
    prefix
    for prefixes in PRODUCT_KIND_PREFIXES.values()
    for prefix in prefixes
)


def correct_query(text: str) -> str:
    words = normalize(text).split()
    return " ".join(QUERY_CORRECTIONS.get(word, word) for word in words)


def _has_prefix(text: str, prefixes: tuple[str, ...]) -> bool:
    return any(
        word.startswith(prefix)
        for word in tokens(text)
        for prefix in prefixes
    )


def looks_like_tour_request(text: str) -> bool:
    return _has_prefix(text, TOUR_CONTEXT_PREFIXES)


def _content_tokens(query: str, page_type: str) -> list[str]:
    result: list[str] = []

    for word in tokens(query):
        if page_type == "tour" and any(
            word.startswith(prefix)
            for prefix in TOUR_CONTEXT_PREFIXES
        ):
            continue

        if page_type == "product" and any(
            word.startswith(prefix)
            for prefix in PRODUCT_CONTEXT_PREFIXES
        ):
            continue

        result.append(word)

    return result


@dataclass(frozen=True)
class Route:
    intent: Intent
    confidence: float
    reason: str
    matched_title: str | None = None
    matched_url: str | None = None
    alternatives: tuple[tuple[str, str], ...] = ()
    matched_note: str | None = None


def normalize(text: str) -> str:
    return normalize_search_text(text)


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
    product_kind: str | None = None,
    product_entities: tuple[str, ...] = (),
    product_usages: tuple[str, ...] = (),
    product_materials: tuple[str, ...] = (),
    product_dimensions_cm: tuple[float, ...] = (),
    product_point_counts: tuple[int, ...] = (),
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
        "product_kind": _canonical_product_kind(product_kind),
        "product_entities": {
            normalize(entity)
            for entity in product_entities
        },
        "product_usages": set(product_usages),
        "product_materials": {
            normalize(material)
            for material in product_materials
        },
        "product_dimensions_cm": tuple(product_dimensions_cm),
        "product_point_counts": tuple(product_point_counts),
    }


@lru_cache(maxsize=1)
def catalog_index() -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {
        "product": [],
        "tour": [],
    }

    for product in ProductRepository().list_all():
        title = product.title or ""
        category = getattr(product, "category", "") or ""
        description = getattr(product, "description", "") or ""
        material = getattr(product, "material", "") or ""
        keywords = getattr(product, "keywords", []) or []
        sku = getattr(product, "sku", "") or ""

        product_features = extract_product_features(
            " ".join([title, description, category])
        )
        profile = _safe_get_product_profile(product.url)

        if profile is not None:
            product_kind = _canonical_product_kind(
                profile.product_type
            )
            entities = profile.entities
            usages = profile.usages
            materials = profile.materials
            profile_text = profile.to_search_text()
        else:
            intelligence = analyze_product(
                title=title,
                description=description,
                category=category,
                sku=sku,
            )

            product_kind = (
                _canonical_product_kind(intelligence.product_type)
                or detect_product_kind(
                    " ".join(
                        part
                        for part in [
                            title,
                            category,
                            description,
                        ]
                        if part
                    )
                )
            )
            entities = intelligence.entities
            usages = intelligence.usages
            materials = intelligence.materials
            profile_text = intelligence.to_search_text()

        index["product"].append(
            _index_item(
                title=title,
                url=product.url,
                searchable_parts=[
                    title,
                    category,
                    description,
                    material,
                    " ".join(keywords),
                    profile_text,
                ],
                product_kind=product_kind,
                product_entities=entities,
                product_usages=usages,
                product_materials=materials,
                product_dimensions_cm=product_features.dimensions_cm,
                product_point_counts=product_features.point_counts,
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



_QUERY_DIMENSION_RE = re.compile(
    r"(?<!\d)(\d{1,3}(?:[.,]\d+)?)\s*(?:см|cm)\b",
    re.IGNORECASE,
)


def _requested_dimension_cm(query: str) -> float | None:
    match = _QUERY_DIMENSION_RE.search(query or "")

    if not match:
        return None

    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _requested_point_count(query: str) -> int | None:
    features = extract_product_features(query)
    return features.point_counts[0] if features.point_counts else None


def _aspect_alternatives(
    requested_aspects: set[str],
    candidates: list[dict],
    limit: int = 6,
) -> tuple[tuple[str, str], ...]:
    if not requested_aspects:
        return ()

    matching = [
        item
        for item in candidates
        if requested_aspects & item.get("product_entities", set())
    ]

    # Show different product types first, then additional options.
    result: list[tuple[str, str]] = []
    seen_types: set[str] = set()

    for item in matching:
        product_type = item.get("product_kind") or "unknown"

        if product_type in seen_types:
            continue

        result.append((item["title"], item["url"]))
        seen_types.add(product_type)

        if len(result) >= limit:
            return tuple(result)

    for item in matching:
        pair = (item["title"], item["url"])

        if pair not in result:
            result.append(pair)

        if len(result) >= limit:
            break

    return tuple(result)

def best_catalog_match(
    query: str,
    page_type: str,
) -> tuple[float, dict | None]:
    query_tokens = _content_tokens(query, page_type)
    query_stems = {stem(word) for word in query_tokens}
    semantics = analyze_query_semantics(query)

    requested_product_kind = (
        semantics["product_kind"]
        if page_type == "product"
        else None
    )
    requested_entities = (
        semantics["entities"]
        if page_type == "product"
        else set()
    )
    requested_usages = (
        semantics["usages"]
        if page_type == "product"
        else set()
    )
    requested_materials = (
        semantics["materials"]
        if page_type == "product"
        else set()
    )
    requested_dimension = (
        _requested_dimension_cm(query)
        if page_type == "product"
        else None
    )
    requested_point_count = (
        _requested_point_count(query)
        if page_type == "product"
        else None
    )

    candidates = catalog_index().get(page_type, [])

    if requested_product_kind:
        candidates = [
            item
            for item in candidates
            if item.get("product_kind") == requested_product_kind
        ]

    if not candidates:
        return 0.0, None

    # A named Buddhist entity is a hard constraint. It is safer to say that
    # no exact item was found than to replace Chenrezig with another deity.
    if requested_entities:
        entity_candidates = [
            item
            for item in candidates
            if requested_entities & item.get("product_entities", set())
        ]

        if not entity_candidates:
            return 0.0, None

        candidates = entity_candidates

    if requested_dimension is not None:
        dimension_candidates = [
            item
            for item in candidates
            if (
                (distance := dimension_distance(
                    requested_dimension,
                    item.get("product_dimensions_cm", ()),
                ))
                is not None
                and distance <= 5
            )
        ]

        if dimension_candidates:
            candidates = dimension_candidates

    # A request containing only a product type may safely return the first
    # item within that exact type.
    if (
        page_type == "product"
        and requested_product_kind
        and not query_tokens
        and not requested_entities
        and not requested_usages
        and not requested_materials
    ):
        return 40.0, candidates[0]

    if not query_tokens and not (
        requested_entities
        or requested_usages
        or requested_materials
    ):
        return 0.0, None

    best_score = 0.0
    best_item = None

    for item in candidates:
        score = 0.0
        semantic_hits = 0

        item_entities = item.get("product_entities", set())
        item_usages = item.get("product_usages", set())
        item_materials = item.get("product_materials", set())

        entity_hits = len(requested_entities & item_entities)
        usage_hits = len(requested_usages & item_usages)
        material_hits = len(requested_materials & item_materials)

        dimension_match = None

        if requested_dimension is not None:
            dimension_match = dimension_distance(
                requested_dimension,
                item.get("product_dimensions_cm", ()),
            )

            if dimension_match is not None:
                if dimension_match == 0:
                    score += 260
                    semantic_hits += 1
                elif dimension_match <= 5:
                    score += 220 - dimension_match * 20
                    semantic_hits += 1
                elif dimension_match <= 10:
                    score += 70 - dimension_match * 4

        if requested_point_count is not None:
            point_counts = item.get("product_point_counts", ())

            if requested_point_count in point_counts:
                score += 220
                semantic_hits += 1
            elif point_counts:
                score -= 180

        if entity_hits:
            score += entity_hits * 160
            semantic_hits += entity_hits

        if usage_hits:
            score += usage_hits * 110
            semantic_hits += usage_hits

        if material_hits:
            score += material_hits * 70
            semantic_hits += material_hits

        title_stems = item["title_stems"]
        search_stems = item["search_stems"]

        exact_title_hits = len(query_stems & title_stems)
        search_hits = len(query_stems & search_stems)

        score += exact_title_hits * 70
        score += max(0, search_hits - exact_title_hits) * 25

        title_tokens = item["title_tokens"]

        if _contains_token_phrase(query_tokens, title_tokens):
            score += 140

        if _contains_token_phrase(title_tokens, query_tokens):
            score += 100

        fuzzy_hits = 0

        for query_word in query_tokens:
            best_ratio = max(
                (
                    _fuzzy_ratio(query_word, title_word)
                    for title_word in title_tokens
                ),
                default=0.0,
            )

            if best_ratio >= 0.88:
                score += 40
                fuzzy_hits += 1
            elif best_ratio >= 0.78:
                score += 20
                fuzzy_hits += 1

        # No random fallback: a candidate needs lexical or semantic evidence.
        if (
            exact_title_hits == 0
            and search_hits == 0
            and fuzzy_hits == 0
            and semantic_hits == 0
        ):
            continue

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
    normalized = correct_query(text)

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

    requested_product_kind = detect_product_kind(normalized)
    product_context = (
        requested_product_kind is not None
        or looks_like_store_request(normalized)
    )
    tour_context = looks_like_tour_request(normalized)

    product_score, product = best_catalog_match(
        normalized,
        "product",
    )
    tour_score, tour = best_catalog_match(
        normalized,
        "tour",
    )

    # Explicit travel language wins over products that merely mention
    # the same country in their title or description.
    if tour_context:
        if tour and tour_score >= 20:
            return Route(
                "tour",
                min(0.99, 0.65 + tour_score / 200),
                "dynamic_tour_match",
                tour["title"],
                tour["url"],
            )

        return Route(
            "tour",
            0.88,
            "generic_tour_request",
        )

    if product_context:
        if product and product_score >= 20:
            semantics = analyze_query_semantics(normalized)
            requested_aspects = semantics["entities"]
            alternatives = _aspect_alternatives(
                requested_aspects,
                catalog_index().get("product", []),
            )
            requested_points = _requested_point_count(normalized)
            note = None

            if (
                requested_points is not None
                and requested_points
                not in product.get("product_point_counts", ())
            ):
                note = (
                    f"В описании товара не указано, что он "
                    f"{requested_points}-конечный."
                )

            return Route(
                "product",
                min(0.99, 0.65 + product_score / 200),
                "dynamic_product_match",
                product["title"],
                product["url"],
                alternatives,
                note,
            )

        return Route(
            "product",
            0.82,
            "store_request_without_match",
        )

    if product and product_score >= 30:
        if product_score >= tour_score:
            semantics = analyze_query_semantics(normalized)
            alternatives = _aspect_alternatives(
                semantics["entities"],
                catalog_index().get("product", []),
            )
            requested_points = _requested_point_count(normalized)
            note = None

            if (
                requested_points is not None
                and requested_points
                not in product.get("product_point_counts", ())
            ):
                note = (
                    f"В описании товара не указано, что он "
                    f"{requested_points}-конечный."
                )

            return Route(
                "product",
                min(0.99, 0.65 + product_score / 200),
                "dynamic_product_match",
                product["title"],
                product["url"],
                alternatives,
                note,
            )

    if tour and tour_score >= 30:
        if tour_score > product_score:
            return Route(
                "tour",
                min(0.99, 0.65 + tour_score / 200),
                "dynamic_tour_match",
                tour["title"],
                tour["url"],
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
