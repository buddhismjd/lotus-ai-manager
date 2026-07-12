from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


class CatalogItemType(StrEnum):
    PRODUCT = "product"
    TOUR = "tour"
    PSYCHOLOGIST_SERVICE = "psychologist_service"


ALLOWED_CATALOG_ITEM_TYPES = frozenset(CatalogItemType)


@dataclass(frozen=True, slots=True)
class CatalogItem:
    """Unified read model for AI Bodhi's commercial knowledge boundary."""

    id: str
    item_type: CatalogItemType
    title: str
    url: str
    summary: str = ""
    status: str = "published"
    tags: tuple[str, ...] = ()
    price: Decimal | None = None
    currency: str = "RUR"
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.item_type not in ALLOWED_CATALOG_ITEM_TYPES:
            raise ValueError(f"Unsupported catalog item type: {self.item_type}")
        if not self.id.strip():
            raise ValueError("Catalog item id must not be empty")
        if not self.title.strip():
            raise ValueError("Catalog item title must not be empty")
        if not self.url.strip():
            raise ValueError("Catalog item url must not be empty")


@dataclass(frozen=True, slots=True)
class CatalogQuery:
    item_types: tuple[CatalogItemType, ...] = ()
    text: str = ""
    tags: tuple[str, ...] = ()
    published_only: bool = True
    limit: int = 20

    def __post_init__(self) -> None:
        unsupported = set(self.item_types) - ALLOWED_CATALOG_ITEM_TYPES
        if unsupported:
            raise ValueError(f"Unsupported catalog item types: {unsupported}")
        if self.limit < 1 or self.limit > 100:
            raise ValueError("Catalog query limit must be between 1 and 100")


@runtime_checkable
class UnifiedCatalogContract(Protocol):
    """Read-only contract used by Sales Advisor and future Knowledge API."""

    def get_item(
        self,
        item_type: CatalogItemType,
        item_id: str,
    ) -> CatalogItem | None: ...

    def list_items(
        self,
        query: CatalogQuery | None = None,
    ) -> list[CatalogItem]: ...

    def search(
        self,
        query: CatalogQuery,
    ) -> list[CatalogItem]: ...

    def recommendation_candidates(
        self,
        source: CatalogItem,
        *,
        limit: int = 10,
    ) -> list[CatalogItem]: ...
