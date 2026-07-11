from __future__ import annotations

import re
from dataclasses import dataclass


_DIMENSION_RE = re.compile(
    r"(?<!\d)(?P<value>\d{1,3}(?:[.,]\d+)?)\s*(?:см|cm)\b",
    re.IGNORECASE,
)

_APPROXIMATE_RE = re.compile(
    r"\b(?:около|примерно|приблизительно|порядка)\b",
    re.IGNORECASE,
)

_POINT_WORDS: dict[int, tuple[str, ...]] = {
    3: ("трехконеч", "трёхконеч"),
    4: ("четырехконеч", "четырёхконеч"),
    5: ("пятиконеч",),
    6: ("шестиконеч",),
    7: ("семиконеч",),
    8: ("восьмиконеч",),
    9: ("девятиконеч",),
}


@dataclass(frozen=True, slots=True)
class ProductFeatures:
    dimensions_cm: tuple[float, ...] = ()
    point_counts: tuple[int, ...] = ()
    approximate_dimension: bool = False


def extract_dimensions_cm(text: str) -> tuple[float, ...]:
    values: list[float] = []

    for match in _DIMENSION_RE.finditer(text or ""):
        raw = match.group("value").replace(",", ".")

        try:
            value = float(raw)
        except ValueError:
            continue

        if 0 < value <= 500:
            values.append(value)

    return tuple(dict.fromkeys(values))


def extract_point_counts(text: str) -> tuple[int, ...]:
    normalized = (text or "").lower().replace("ё", "е")
    result: list[int] = []

    for count, roots in _POINT_WORDS.items():
        if any(root.replace("ё", "е") in normalized for root in roots):
            result.append(count)

    numeric_patterns = (
        r"(?<!\d)(\d{1,2})\s*[- ]?(?:конечн|лучев)",
        r"(?<!\d)(\d{1,2})\s*(?:зубц|спиц)",
    )

    for pattern in numeric_patterns:
        for match in re.finditer(pattern, normalized):
            value = int(match.group(1))

            if 2 <= value <= 32:
                result.append(value)

    return tuple(dict.fromkeys(result))


def extract_product_features(text: str) -> ProductFeatures:
    return ProductFeatures(
        dimensions_cm=extract_dimensions_cm(text),
        point_counts=extract_point_counts(text),
        approximate_dimension=bool(_APPROXIMATE_RE.search(text or "")),
    )


def dimension_distance(
    requested_cm: float,
    candidate_dimensions: tuple[float, ...],
) -> float | None:
    if not candidate_dimensions:
        return None

    return min(abs(requested_cm - value) for value in candidate_dimensions)


__all__ = [
    "ProductFeatures",
    "dimension_distance",
    "extract_dimensions_cm",
    "extract_point_counts",
    "extract_product_features",
]
