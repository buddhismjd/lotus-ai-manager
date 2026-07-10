from __future__ import annotations

import re
from dataclasses import dataclass

from backend.storage.database import get_connection, initialize_database


STOPWORDS = {
    "что", "как", "где", "когда", "есть", "мне", "можно", "хочу",
    "покажи", "расскажи", "про", "для", "или", "это", "какой", "какая",
}

INTENT_TYPES = {
    "tour": {
        "тур", "поездка", "путешествие", "кайлас", "лапчи",
        "тибет", "непал", "бутан", "индия", "ретрит",
    },
    "product": {
        "товар", "купить", "статуя", "чётки", "четки",
        "серьги", "благовония", "гау", "подвеска",
    },
    "psychologist": {
        "психолог", "консультация", "стресс", "эмоции", "буддолог",
    },
}

ALLOWED_TYPES = {
    "tour": {"tour", "tour_catalog"},
    "product": {"product", "product_catalog", "shop_catalog"},
    "psychologist": {"psychologist"},
}


@dataclass
class SearchResult:
    document_id: str
    title: str
    url: str
    page_type: str
    content: str
    score: float


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]{3,}", text.lower())
    return [word for word in words if word not in STOPWORDS]


def detect_intent(query: str) -> str | None:
    words = set(tokenize(query))
    best_type = None
    best_score = 0

    for page_type, markers in INTENT_TYPES.items():
        score = len(words & markers)

        if score > best_score:
            best_type = page_type
            best_score = score

    return best_type


def search(query: str, limit: int = 5) -> list[SearchResult]:
    initialize_database()
    tokens = tokenize(query)
    intent = detect_intent(query)
    allowed_types = ALLOWED_TYPES.get(intent) if intent else None

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                d.id AS document_id,
                d.title,
                d.url,
                d.page_type,
                d.priority,
                c.content
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE d.enabled = 1
            """
        ).fetchall()

    results: list[SearchResult] = []

    for row in rows:
        if allowed_types and row["page_type"] not in allowed_types:
            continue

        title_lower = row["title"].lower()
        text = f"{row['title']} {row['content']}".lower()
        score = float(row["priority"]) / 20.0

        for token in tokens:
            if token in title_lower:
                score += 8

            if token in text:
                score += 3 + text.count(token)

        if intent:
            if row["page_type"] == intent:
                score += 20
            elif row["page_type"] in allowed_types:
                score += 8

        if score > 0:
            results.append(
                SearchResult(
                    document_id=row["document_id"],
                    title=row["title"],
                    url=row["url"],
                    page_type=row["page_type"],
                    content=row["content"],
                    score=score,
                )
            )

    results.sort(key=lambda item: item.score, reverse=True)

    unique: list[SearchResult] = []
    seen_urls: set[str] = set()

    for result in results:
        if result.url in seen_urls:
            continue

        seen_urls.add(result.url)
        unique.append(result)

        if len(unique) >= limit:
            break

    return unique


def print_results(query: str) -> None:
    results = search(query)

    print(f"Query: {query}")
    print(f"Intent: {detect_intent(query) or 'general'}")
    print()

    if not results:
        print("Nothing found")
        return

    for index, result in enumerate(results, start=1):
        print(f"{index}. [{result.page_type}] {result.title}")
        print(f"   score: {result.score:.1f}")
        print(f"   {result.url}")


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]).strip() or "Есть тур в Индию?"
    print_results(query)
