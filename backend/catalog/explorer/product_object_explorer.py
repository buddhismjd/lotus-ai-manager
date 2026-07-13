from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from backend.storage.database import get_connection, initialize_database


DEFAULT_OUTPUT_DIR = Path("data/product_object_explorer")
_MAX_SAMPLES = 5


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return "string"


def _sample(value: Any) -> Any:
    if isinstance(value, str):
        compact = " ".join(value.split())
        return compact[:180]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return {"items": len(value)}
    if isinstance(value, dict):
        return {"keys": sorted(str(key) for key in value)[:12]}
    return str(value)[:180]


@dataclass(frozen=True, slots=True)
class CatalogExploration:
    generated_at: str
    total_products: int
    valid_products: int
    invalid_products: int
    field_coverage: dict[str, dict[str, Any]]
    schema_tree: dict[str, Any]
    catalog_statistics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "total_products": self.total_products,
            "valid_products": self.valid_products,
            "invalid_products": self.invalid_products,
            "field_coverage": self.field_coverage,
            "schema_tree": self.schema_tree,
            "catalog_statistics": self.catalog_statistics,
        }


def load_raw_products() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Load confirmed raw Tilda product objects from SQLite.

    Malformed rows are returned separately so diagnostics can expose them
    without preventing exploration of the remaining catalog.
    """
    initialize_database()
    products: list[dict[str, Any]] = []
    invalid: list[dict[str, str]] = []

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT product_uid, page_url, raw_json
            FROM product_raw_snapshots
            ORDER BY product_uid
            """
        ).fetchall()

    for row in rows:
        try:
            value = json.loads(row["raw_json"])
            if not isinstance(value, dict):
                raise ValueError("raw_json root is not an object")
            products.append(value)
        except (json.JSONDecodeError, ValueError) as exc:
            invalid.append(
                {
                    "product_uid": str(row["product_uid"]),
                    "page_url": str(row["page_url"]),
                    "error": str(exc),
                }
            )

    return products, invalid


def _walk(
    value: Any,
    path: str,
    seen_paths: set[str],
    non_empty_paths: set[str],
    observations: dict[str, dict[str, Any]],
) -> None:
    if path:
        seen_paths.add(path)
        observation = observations.setdefault(
            path,
            {"types": Counter(), "samples": []},
        )
        observation["types"][_type_name(value)] += 1
        if value not in (None, "", [], {}):
            non_empty_paths.add(path)
        candidate = _sample(value)
        if candidate not in observation["samples"] and len(observation["samples"]) < _MAX_SAMPLES:
            observation["samples"].append(candidate)

    if isinstance(value, dict):
        for key in sorted(value, key=str):
            child_path = f"{path}.{key}" if path else str(key)
            _walk(value[key], child_path, seen_paths, non_empty_paths, observations)
        return

    if isinstance(value, list):
        item_path = f"{path}[]" if path else "[]"
        for item in value:
            _walk(item, item_path, seen_paths, non_empty_paths, observations)


def _tree_insert(root: dict[str, Any], path: str, metadata: dict[str, Any]) -> None:
    node = root
    for segment in path.split("."):
        node = node.setdefault("children", {}).setdefault(segment, {})
    node.update({key: value for key, value in metadata.items() if key != "path"})


def _named_entry_statistics(products: Iterable[dict[str, Any]], field: str) -> dict[str, Any]:
    label_counts: Counter[str] = Counter()
    shape_counts: Counter[str] = Counter()
    products_with_entries = 0
    total_entries = 0

    for product in products:
        entries = product.get(field)
        if not isinstance(entries, list) or not entries:
            continue
        products_with_entries += 1
        for entry in entries:
            total_entries += 1
            if not isinstance(entry, dict):
                shape_counts[_type_name(entry)] += 1
                continue
            shape_counts["|".join(sorted(str(key) for key in entry)) or "<empty>"] += 1
            label = (
                entry.get("title")
                or entry.get("name")
                or entry.get("label")
                or entry.get("key")
            )
            if label not in (None, ""):
                label_counts[str(label).strip()] += 1

    return {
        "products_with_entries": products_with_entries,
        "total_entries": total_entries,
        "labels": dict(label_counts.most_common()),
        "shapes": dict(shape_counts.most_common()),
    }


def explore_product_objects(
    products: Iterable[dict[str, Any]],
    *,
    invalid_products: int = 0,
) -> CatalogExploration:
    product_list = list(products)
    observations: dict[str, dict[str, Any]] = {}
    coverage_counts: Counter[str] = Counter()
    non_empty_counts: Counter[str] = Counter()
    top_level_counts: Counter[str] = Counter()

    for product in product_list:
        seen_paths: set[str] = set()
        non_empty_paths: set[str] = set()
        _walk(product, "", seen_paths, non_empty_paths, observations)
        coverage_counts.update(seen_paths)
        non_empty_counts.update(non_empty_paths)
        top_level_counts.update(str(key) for key in product)

    total = len(product_list)
    field_coverage: dict[str, dict[str, Any]] = {}
    for path in sorted(observations):
        observation = observations[path]
        count = coverage_counts[path]
        field_coverage[path] = {
            "path": path,
            "products": count,
            "coverage_percent": round((count / total * 100), 2) if total else 0.0,
            "non_empty_products": non_empty_counts[path],
            "types": dict(observation["types"].most_common()),
            "samples": observation["samples"],
        }

    schema_tree: dict[str, Any] = {"children": {}}
    for path, metadata in field_coverage.items():
        _tree_insert(schema_tree, path, metadata)

    catalog_statistics = {
        "top_level_fields": dict(top_level_counts.most_common()),
        "characteristics": _named_entry_statistics(product_list, "characteristics"),
        "properties": _named_entry_statistics(product_list, "properties"),
        "editions": _named_entry_statistics(product_list, "editions"),
        "products_with_non_empty_characteristics": sum(
            1 for product in product_list if product.get("characteristics")
        ),
        "products_with_non_empty_properties": sum(
            1 for product in product_list if product.get("properties")
        ),
        "products_with_editions": sum(
            1 for product in product_list if product.get("editions")
        ),
        "all_paths": len(field_coverage),
    }

    return CatalogExploration(
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        total_products=total + invalid_products,
        valid_products=total,
        invalid_products=invalid_products,
        field_coverage=field_coverage,
        schema_tree=schema_tree,
        catalog_statistics=catalog_statistics,
    )


def write_exploration_artifacts(
    exploration: CatalogExploration,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    payloads = {
        "field_coverage": exploration.field_coverage,
        "schema_tree": exploration.schema_tree,
        "catalog_statistics": {
            "generated_at": exploration.generated_at,
            "total_products": exploration.total_products,
            "valid_products": exploration.valid_products,
            "invalid_products": exploration.invalid_products,
            **exploration.catalog_statistics,
        },
    }
    paths: dict[str, Path] = {}
    for name, payload in payloads.items():
        path = destination / f"{name}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        paths[name] = path
    return paths


def run_product_object_explorer(
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> tuple[CatalogExploration, dict[str, Path], list[dict[str, str]]]:
    products, invalid = load_raw_products()
    exploration = explore_product_objects(
        products,
        invalid_products=len(invalid),
    )
    paths = write_exploration_artifacts(exploration, output_dir)
    return exploration, paths, invalid


__all__ = [
    "CatalogExploration",
    "DEFAULT_OUTPUT_DIR",
    "explore_product_objects",
    "load_raw_products",
    "run_product_object_explorer",
    "write_exploration_artifacts",
]
