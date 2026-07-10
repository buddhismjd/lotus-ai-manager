from __future__ import annotations

import json
import re
from dataclasses import dataclass
from math import inf

from backend.config import KNOWLEDGE_FILE


CATEGORY_ALIASES = {
    "statue": {
        "статуя", "статуи", "скульптура", "фигура", "будда",
        "ушнишавиджая", "тара", "гуру ринпоче",
    },
    "vajra": {
        "ваджра", "дордже",
    },
    "mala": {
        "четки", "чётки", "мала",
    },
    "earrings": {
        "серьги", "сережки", "серёжки",
    },
    "pendant": {
        "подвеска", "подвески", "кулон",
    },
    "gau": {
        "гау", "реликварий",
    },
    "incense": {
        "благовония", "благовоние", "аромапалочки",
    },
}

CATEGORY_YML_WORDS = {
    "statue": {"статуи", "статуя"},
    "vajra": {"ваджра", "ваджры", "ритуальные предметы"},
    "mala": {"четки", "чётки", "мала"},
    "earrings": {"серьги"},
    "pendant": {"подвески", "подвеска"},
    "gau": {"гау"},
    "incense": {"благовония"},
}

ENTITY_ALIASES = {
    "buddha": {
        "будда", "будды", "шакьямуни", "амитабха",
        "медицины", "акшобхья",
    },
    "tara": {
        "тара", "тары", "зеленая тара", "зелёная тара",
        "белая тара",
    },
    "ushnishavijaya": {
        "ушнишавиджая", "ушнишавиджаи",
    },
    "vajra": {
        "ваджра", "дордже",
    },
}

MATERIAL_ALIASES = {
    "silver": {"серебро", "серебряный", "серебряные"},
    "bronze": {"бронза", "бронзовый", "бронзовая"},
    "copper": {"медь", "медный", "медная"},
    "wood": {"дерево", "деревянный", "деревянная"},
    "stone": {"камень", "каменный", "натуральный камень"},
}

STOPWORDS = {
    "есть", "нужна", "нужен", "нужно", "хочу", "купить",
    "около", "примерно", "приблизительно", "вас", "мне",
    "товар", "покажите", "покажи",
}


@dataclass
class ProductQuery:
    raw: str
    category: str | None
    entity: str | None
    material: str | None
    target_size_cm: float | None
    max_price: float | None
    min_price: float | None
    terms: list[str]


@dataclass
class ProductMatch:
    page: dict
    score: float
    size_cm: float | None
    size_difference: float | None
    reasons: list[str]


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        (text or "").lower().replace("ё", "е"),
    ).strip()


def detect_alias(
    text: str,
    aliases: dict[str, set[str]],
) -> str | None:
    normalized = normalize(text)
    best: tuple[int, str] | None = None

    for key, values in aliases.items():
        for value in values:
            candidate = normalize(value)

            if candidate in normalized:
                match = (len(candidate), key)

                if best is None or match[0] > best[0]:
                    best = match

    return best[1] if best else None


def extract_target_size(text: str) -> float | None:
    normalized = normalize(text)

    patterns = (
        r"(?:около|примерно|приблизительно|порядка)\s*(\d+(?:[.,]\d+)?)\s*см",
        r"(\d+(?:[.,]\d+)?)\s*см",
    )

    for pattern in patterns:
        match = re.search(pattern, normalized)

        if match:
            return float(match.group(1).replace(",", "."))

    return None


def extract_price_limit(
    text: str,
) -> tuple[float | None, float | None]:
    normalized = normalize(text)

    max_match = re.search(
        r"(?:до|не дороже)\s*(\d[\d\s]*)\s*(?:руб|₽)",
        normalized,
    )
    min_match = re.search(
        r"(?:от|не дешевле)\s*(\d[\d\s]*)\s*(?:руб|₽)",
        normalized,
    )

    maximum = (
        float(max_match.group(1).replace(" ", ""))
        if max_match
        else None
    )
    minimum = (
        float(min_match.group(1).replace(" ", ""))
        if min_match
        else None
    )

    return minimum, maximum


def tokenize(text: str) -> list[str]:
    words = re.findall(
        r"[a-zA-Zа-яА-ЯёЁ0-9]{3,}",
        normalize(text),
    )
    return [
        word
        for word in words
        if word not in STOPWORDS
        and not word.isdigit()
    ]


def parse_product_query(text: str) -> ProductQuery:
    minimum, maximum = extract_price_limit(text)

    return ProductQuery(
        raw=text,
        category=detect_alias(text, CATEGORY_ALIASES),
        entity=detect_alias(text, ENTITY_ALIASES),
        material=detect_alias(text, MATERIAL_ALIASES),
        target_size_cm=extract_target_size(text),
        max_price=maximum,
        min_price=minimum,
        terms=tokenize(text),
    )


def load_products() -> list[dict]:
    if not KNOWLEDGE_FILE.exists():
        return []

    data = json.loads(
        KNOWLEDGE_FILE.read_text(encoding="utf-8")
    )

    return [
        page
        for page in data.get("pages", [])
        if page.get("page_type") == "product"
        and page.get("enabled", True)
    ]


def page_text(page: dict) -> str:
    params = page.get("params") or {}

    if isinstance(params, dict):
        params_text = " ".join(
            f"{key} {value}"
            for key, value in params.items()
        )
    else:
        params_text = ""

    return normalize(
        " ".join(
            [
                str(page.get("title", "")),
                str(page.get("category", "")),
                str(page.get("text", "")),
                params_text,
            ]
        )
    )


def page_category(page: dict) -> str | None:
    text = page_text(page)
    category = normalize(str(page.get("category", "")))

    for key, aliases in CATEGORY_YML_WORDS.items():
        if any(
            normalize(alias) in category
            for alias in aliases
        ):
            return key

    return detect_alias(text, CATEGORY_ALIASES)


def extract_product_sizes(page: dict) -> list[float]:
    text = page_text(page)
    values: list[float] = []

    patterns = (
        r"(?:высота|размер|длина|диаметр)\s*[:\-]?\s*(\d+(?:[.,]\d+)?)\s*см",
        r"(\d+(?:[.,]\d+)?)\s*[xх×]\s*\d+(?:[.,]\d+)?\s*см",
        r"(\d+(?:[.,]\d+)?)\s*см",
    )

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            value = float(
                match.group(1).replace(",", ".")
            )

            if 1 <= value <= 300:
                values.append(value)

    return sorted(set(values))


def product_price(page: dict) -> float | None:
    raw = str(page.get("price", "")).strip()

    if not raw:
        match = re.search(
            r"цена\s*[:\-]?\s*(\d[\d\s]*(?:[.,]\d+)?)",
            page_text(page),
        )

        if not match:
            return None

        raw = match.group(1)

    cleaned = raw.replace(" ", "").replace(",", ".")

    try:
        return float(cleaned)
    except ValueError:
        return None


def matches_entity(
    page: dict,
    entity: str,
) -> bool:
    text = page_text(page)
    return any(
        normalize(alias) in text
        for alias in ENTITY_ALIASES.get(entity, set())
    )


def matches_material(
    page: dict,
    material: str,
) -> bool:
    text = page_text(page)
    return any(
        normalize(alias) in text
        for alias in MATERIAL_ALIASES.get(material, set())
    )


def score_product(
    page: dict,
    query: ProductQuery,
) -> ProductMatch | None:
    text = page_text(page)
    title = normalize(str(page.get("title", "")))
    category = page_category(page)
    price = product_price(page)
    reasons: list[str] = []
    score = 0.0

    if query.category:
        if category == query.category:
            score += 60
            reasons.append("совпадает категория")
        else:
            return None

    if query.entity:
        if matches_entity(page, query.entity):
            score += 45
            reasons.append("совпадает объект")
        else:
            # Для точного запроса «Будда» не выдаём Тару или серьги.
            return None

    if query.material:
        if matches_material(page, query.material):
            score += 25
            reasons.append("совпадает материал")
        else:
            return None

    if query.max_price is not None:
        if price is None or price > query.max_price:
            return None

        score += 15
        reasons.append("подходит по цене")

    if query.min_price is not None:
        if price is None or price < query.min_price:
            return None

        score += 15
        reasons.append("подходит по цене")

    for term in query.terms:
        normalized_term = normalize(term)

        if normalized_term in title:
            score += 10
        elif normalized_term in text:
            score += 3

    sizes = extract_product_sizes(page)
    selected_size = None
    size_difference = None

    if query.target_size_cm is not None:
        if not sizes:
            score -= 8
        else:
            selected_size = min(
                sizes,
                key=lambda value: abs(
                    value - query.target_size_cm
                ),
            )
            size_difference = abs(
                selected_size - query.target_size_cm
            )

            if size_difference <= 2:
                score += 35
                reasons.append("размер очень близкий")
            elif size_difference <= 5:
                score += 22
                reasons.append("размер близкий")
            elif size_difference <= 10:
                score += 8
                reasons.append("размер приблизительно подходит")
            else:
                score -= min(size_difference, 25)

    if score <= 0:
        return None

    return ProductMatch(
        page=page,
        score=score,
        size_cm=selected_size,
        size_difference=size_difference,
        reasons=reasons,
    )


def search_products(
    text: str,
    limit: int = 5,
) -> tuple[ProductQuery, list[ProductMatch]]:
    query = parse_product_query(text)
    matches: list[ProductMatch] = []

    for product in load_products():
        match = score_product(product, query)

        if match:
            matches.append(match)

    matches.sort(
        key=lambda item: (
            -item.score,
            item.size_difference
            if item.size_difference is not None
            else inf,
            normalize(str(item.page.get("title", ""))),
        )
    )

    return query, matches[:limit]


def format_price(page: dict) -> str | None:
    value = page.get("price")

    if value in (None, ""):
        return None

    currency = str(
        page.get("currency") or "RUR"
    ).upper()

    currency_label = {
        "RUR": "₽",
        "RUB": "₽",
        "USD": "$",
        "EUR": "€",
    }.get(currency, currency)

    try:
        number = float(str(value).replace(",", "."))
        formatted = (
            f"{number:,.0f}"
            .replace(",", " ")
        )
        return f"{formatted} {currency_label}"
    except ValueError:
        return f"{value} {currency_label}".strip()


if __name__ == "__main__":
    import sys

    question = (
        " ".join(sys.argv[1:]).strip()
        or "У вас есть статуя Будды около 20 см?"
    )

    parsed, results = search_products(question)

    print("Parsed query:")
    print(parsed)
    print()

    for result in results:
        print(
            f"{result.score:.1f} | "
            f"{result.page.get('title')} | "
            f"{format_price(result.page)} | "
            f"{result.size_cm} см | "
            f"{result.page.get('url')}"
        )
