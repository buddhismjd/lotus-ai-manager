from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from dataclasses import dataclass
from typing import Iterable

from backend.catalog.models import Product
from backend.catalog.product_features import extract_dimensions_cm
from backend.catalog.product_intelligence import analyze_product, normalize
from backend.catalog.repositories import ProductRepository


_COLLECTION_CONFIG = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "product_collection_pages.json"
)


@lru_cache(maxsize=1)
def _collection_pages() -> dict[str, dict[str, str]]:
    try:
        loaded = json.loads(_COLLECTION_CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        loaded = {}
    return loaded if isinstance(loaded, dict) else {}


_RANGE_RE = re.compile(
    r"(?<!\d)(?P<minimum>\d{1,3}(?:[.,]\d+)?)\s*"
    r"(?:-|–|—|до)\s*"
    r"(?P<maximum>\d{1,3}(?:[.,]\d+)?)\s*(?:см|cm)\b",
    re.IGNORECASE,
)
_EXACT_RE = re.compile(
    r"(?<!\d)(?P<value>\d{1,3}(?:[.,]\d+)?)\s*(?:см|cm)\b",
    re.IGNORECASE,
)
_HEIGHT_VALUE_RE = re.compile(
    r"\b(?:высота|высотой|высоту)\s*[:=-]?\s*(?P<value>\d{1,3}(?:[.,]\d+)?)\s*(?:см|cm)\b",
    re.IGNORECASE,
)
_APPROXIMATE_RE = re.compile(
    r"\b(?:около|примерно|приблизительно|порядка)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ProductSelectionRequest:
    category: str
    category_label: str
    aspect: str | None = None
    height_min_cm: float | None = None
    height_max_cm: float | None = None

    @property
    def has_height(self) -> bool:
        return self.height_min_cm is not None and self.height_max_cm is not None

    @property
    def height_label(self) -> str | None:
        if not self.has_height:
            return None
        assert self.height_min_cm is not None
        assert self.height_max_cm is not None
        if abs(self.height_min_cm - self.height_max_cm) < 0.01:
            return f"{self.height_min_cm:g} см"
        return f"{self.height_min_cm:g}–{self.height_max_cm:g} см"


@dataclass(frozen=True, slots=True)
class ProductSelectionResult:
    request: ProductSelectionRequest
    products: tuple[Product, ...]


def parse_product_selection_request(text: str) -> ProductSelectionRequest | None:
    intelligence = analyze_product(title=text)
    product_type = intelligence.product_type
    if product_type not in {"statue", "thangka"}:
        return None

    aspect = intelligence.entities[0] if intelligence.entities else None
    minimum: float | None = None
    maximum: float | None = None

    range_match = _RANGE_RE.search(text or "")
    if range_match:
        first = float(range_match.group("minimum").replace(",", "."))
        second = float(range_match.group("maximum").replace(",", "."))
        minimum, maximum = sorted((first, second))
    else:
        exact_match = _EXACT_RE.search(text or "")
        if exact_match:
            value = float(exact_match.group("value").replace(",", "."))
            if _APPROXIMATE_RE.search(text or ""):
                minimum = max(0.1, value - 2.0)
                maximum = value + 2.0
            else:
                minimum = value
                maximum = value

    return ProductSelectionRequest(
        category=product_type,
        category_label="статуи" if product_type == "statue" else "тханки",
        aspect=aspect,
        height_min_cm=minimum,
        height_max_cm=maximum,
    )


class ProductSelectionService:
    """Structured selection for statues and thangkas from the product catalog."""

    def __init__(self, repository: ProductRepository | None = None) -> None:
        self._products = repository or ProductRepository()

    def select(self, request: ProductSelectionRequest) -> ProductSelectionResult:
        matches: list[Product] = []
        for product in self._products.list_all():
            intelligence = analyze_product(
                title=product.title,
                description=product.description,
                category=product.category or "",
            )
            if intelligence.product_type != request.category:
                continue
            if request.aspect and not self._matches_aspect(
                request.aspect,
                intelligence.entities,
                product,
            ):
                continue
            if request.has_height and not self._matches_height(product, request):
                continue
            matches.append(product)

        matches.sort(key=lambda item: (self._primary_height(item) is None, self._primary_height(item) or 0, item.title))
        return ProductSelectionResult(request=request, products=tuple(matches))

    @staticmethod
    def collection_link(category: str) -> tuple[str, str]:
        pages = _collection_pages()
        page = pages.get(category) or pages.get("default") or {}
        return (
            str(page.get("label") or "Перейти в магазин"),
            str(page.get("url") or "https://svet-lotosa.tilda.ws/svet-lotosa-shop"),
        )

    @staticmethod
    def _matches_aspect(
        requested: str,
        product_entities: Iterable[str],
        product: Product,
    ) -> bool:
        wanted = normalize(requested)
        entities = {normalize(value) for value in product_entities}
        if wanted in entities:
            return True
        haystack = normalize(f"{product.title} {product.description}")
        return wanted in haystack

    @staticmethod
    def heights_for(product: Product) -> tuple[float, ...]:
        values: list[float] = []
        if product.height_cm is not None:
            values.append(float(product.height_cm))
        source = f"{product.title}\n{product.description}"
        explicit_heights = [
            float(match.group("value").replace(",", "."))
            for match in _HEIGHT_VALUE_RE.finditer(source)
        ]
        if explicit_heights:
            values.extend(explicit_heights)
        else:
            values.extend(extract_dimensions_cm(source))
        return tuple(dict.fromkeys(value for value in values if 0 < value <= 500))

    @classmethod
    def _matches_height(
        cls,
        product: Product,
        request: ProductSelectionRequest,
    ) -> bool:
        assert request.height_min_cm is not None
        assert request.height_max_cm is not None
        dimensions = cls.heights_for(product)
        if not dimensions:
            return False
        tolerance = 0.25 if request.height_min_cm == request.height_max_cm else 0.0
        return any(
            request.height_min_cm - tolerance <= value <= request.height_max_cm + tolerance
            for value in dimensions
        )

    @classmethod
    def _primary_height(cls, product: Product) -> float | None:
        dimensions = cls.heights_for(product)
        return dimensions[0] if dimensions else None


__all__ = [
    "ProductSelectionRequest",
    "ProductSelectionResult",
    "ProductSelectionService",
    "parse_product_selection_request",
]
