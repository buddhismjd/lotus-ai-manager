from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from backend.integrations.tilda_store_api import StoreProduct
from backend.integrations.tilda_store_multi_sync import StorePartResult


@dataclass(frozen=True, slots=True)
class CatalogCompletenessReport:
    unique_products: int
    configured_store_blocks: int
    successful_store_blocks: int
    failed_store_blocks: int
    expected_products_total: int | None
    received_products_total: int
    duplicate_products_across_blocks: int
    uncategorized_products: int
    missing_titles: int
    missing_urls: int
    category_counts: dict[str, int]
    complete: bool
    warnings: tuple[str, ...]
    source_pages_checked: int = 0
    source_pages_failed: int = 0


def build_catalog_completeness_report(
    products: Iterable[StoreProduct],
    part_results: Iterable[StorePartResult],
    *,
    configured_store_blocks: int,
    duplicate_products_across_blocks: int = 0,
    source_reports: Iterable[object] = (),
) -> CatalogCompletenessReport:
    product_list = list(products)
    parts = list(part_results)
    successful = [part for part in parts if not part.error]
    failed = [part for part in parts if part.error]
    known_expected = [part.expected_total for part in successful if part.expected_total is not None]
    expected_total = sum(known_expected) if len(known_expected) == len(successful) and successful else None
    received_total = sum(part.received_total for part in successful)

    category_counts = Counter(
        (product.category or "Без категории").strip() or "Без категории"
        for product in product_list
    )
    uncategorized = category_counts.get("Без категории", 0)
    missing_titles = sum(1 for product in product_list if not product.title.strip())
    missing_urls = sum(1 for product in product_list if not product.url.strip())

    source_reports = list(source_reports)
    source_failures = [r for r in source_reports if getattr(r, "required", False) and (getattr(r, "error", None) or not getattr(r, "html_loaded", False))]
    warnings: list[str] = []
    if source_failures:
        warnings.append(f"Не удалось проверить обязательных страниц каталога: {len(source_failures)}.")
    if configured_store_blocks == 0:
        warnings.append("Не настроен ни один блок магазина Tilda.")
    if failed:
        warnings.append(f"Не удалось загрузить блоков магазина: {len(failed)}.")
    for part in successful:
        if part.expected_total is not None and part.received_total != part.expected_total:
            warnings.append(
                "Неполный блок магазина "
                f"recid={part.recid}: получено {part.received_total} "
                f"из {part.expected_total}."
            )
    if expected_total is not None and received_total != expected_total:
        warnings.append(
            f"Суммарно получено {received_total} из ожидаемых {expected_total} товаров."
        )
    if not product_list:
        warnings.append("Каталог не содержит товаров.")
    if uncategorized:
        warnings.append(f"Товаров без категории: {uncategorized}.")
    if missing_titles:
        warnings.append(f"Товаров без названия: {missing_titles}.")
    if missing_urls:
        warnings.append(f"Товаров без ссылки: {missing_urls}.")
    if duplicate_products_across_blocks:
        warnings.append(
            "Одинаковые товары встретились в нескольких блоках: "
            f"{duplicate_products_across_blocks}. Они были объединены по UID."
        )

    complete = bool(product_list) and not failed and not source_failures and not any(
        "Неполный блок" in warning or "Суммарно получено" in warning
        for warning in warnings
    )
    return CatalogCompletenessReport(
        unique_products=len(product_list),
        configured_store_blocks=configured_store_blocks,
        successful_store_blocks=len(successful),
        failed_store_blocks=len(failed),
        expected_products_total=expected_total,
        received_products_total=received_total,
        duplicate_products_across_blocks=duplicate_products_across_blocks,
        uncategorized_products=uncategorized,
        missing_titles=missing_titles,
        missing_urls=missing_urls,
        category_counts=dict(sorted(category_counts.items())),
        complete=complete,
        warnings=tuple(warnings),
        source_pages_checked=len(source_reports),
        source_pages_failed=len(source_failures),
    )
