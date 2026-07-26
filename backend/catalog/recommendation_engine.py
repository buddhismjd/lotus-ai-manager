from __future__ import annotations

from dataclasses import dataclass

from backend.catalog.product_intelligence import normalize


_RECOMMENDATION_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("gift", ("подар", "в подарок")),
    ("home_altar", ("домашн алтар", "для алтар", "на алтар")),
)

_EXHAUSTIVE_MARKERS = (
    "все",
    "весь",
    "вся",
    "всё",
    "что-нибудь с",
    "что нибудь с",
    "покажи все",
    "покажите все",
)


@dataclass(frozen=True, slots=True)
class RecommendationQuery:
    """Deterministic commercial-selection intent extracted from a query.

    This model is intentionally narrow: it only describes purposes that can be
    supported by the product catalog.  It never recommends Buddhist practices
    or produces informational guidance outside the site's offers.
    """

    usage: str | None = None
    exhaustive: bool = False
    result_limit: int | None = None

    @property
    def is_recommendation(self) -> bool:
        return self.usage is not None


def analyze_recommendation_query(query: str) -> RecommendationQuery:
    text = normalize(query)
    exhaustive = any(marker in text for marker in _EXHAUSTIVE_MARKERS)

    words = text.split()

    def matches(pattern: str) -> bool:
        roots = normalize(pattern).split()
        if not roots:
            return False
        for index in range(len(words) - len(roots) + 1):
            window = words[index:index + len(roots)]
            if all(word.startswith(root) for word, root in zip(window, roots)):
                return True
        return False

    usage = None
    for candidate, patterns in _RECOMMENDATION_PATTERNS:
        if any(matches(pattern) for pattern in patterns):
            usage = candidate
            break

    # Explicit requests for all matching offers must never be truncated.
    result_limit = None if exhaustive or usage is None else 6
    return RecommendationQuery(
        usage=usage,
        exhaustive=exhaustive,
        result_limit=result_limit,
    )


def apply_recommendation_limit(items: list[object], intent: RecommendationQuery) -> list[object]:
    if intent.result_limit is None:
        return items
    return items[: intent.result_limit]


__all__ = [
    "RecommendationQuery",
    "analyze_recommendation_query",
    "apply_recommendation_limit",
]
