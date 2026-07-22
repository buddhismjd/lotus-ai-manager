from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Protocol, TypeVar

_TOKEN_RE = re.compile(r"[0-9a-zа-яё]+", re.IGNORECASE)
_STOP_WORDS = {
    "в", "во", "и", "на", "по", "для", "с", "со", "из", "к", "ко",
    "есть", "нужен", "нужна", "нужны", "покажи", "покажите", "найди",
    "товар", "товары", "тур", "туры", "поездка", "поездки",
}


class RankableCollectionItem(Protocol):
    id: str
    title: str
    description: str | None
    material: str | None
    size: str | None
    availability: str | None


ItemT = TypeVar("ItemT", bound=RankableCollectionItem)


def _tokens(value: str | None) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN_RE.findall(value or "")
        if token.casefold() not in _STOP_WORDS
    }


def relevance_score(query: str, item: RankableCollectionItem) -> int:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 0

    title_tokens = _tokens(item.title)
    description_tokens = _tokens(item.description)
    metadata_tokens = _tokens(" ".join(filter(None, (item.material, item.size, item.availability))))

    normalized_query = " ".join(sorted(query_tokens))
    normalized_title = " ".join(sorted(title_tokens))
    score = 0
    if normalized_query and normalized_query == normalized_title:
        score += 100
    score += 20 * len(query_tokens & title_tokens)
    score += 5 * len(query_tokens & metadata_tokens)
    score += 2 * len(query_tokens & description_tokens)
    return score


def rank_collection(query: str, items: Iterable[ItemT]) -> list[ItemT]:
    return sorted(
        items,
        key=lambda item: (-relevance_score(query, item), item.title.casefold(), item.id),
    )


__all__ = ["rank_collection", "relevance_score"]
