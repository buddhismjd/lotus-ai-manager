from __future__ import annotations

import json

from backend.catalog.explorer.product_object_explorer import (
    explore_product_objects,
    write_exploration_artifacts,
)


PRODUCTS = [
    {
        "uid": 1,
        "title": "Статуя",
        "gallery": [{"img": "one.jpg", "alt": "Фото"}],
        "quantity": "1",
        "characteristics": [
            {"title": "Высота", "value": "12 см"},
            {"title": "Материал", "value": "Бронза"},
        ],
        "properties": [],
        "editions": [{"sku": "A", "quantity": "1", "price": "100"}],
    },
    {
        "uid": 2,
        "title": "Ваджра",
        "gallery": [],
        "quantity": "0",
        "characteristics": [],
        "properties": [{"name": "Страна", "value": "Тибет"}],
        "editions": [{"sku": "B", "quantity": "0", "price": "200"}],
        "future_field": {"nested": True},
    },
]


def test_collects_recursive_field_coverage() -> None:
    result = explore_product_objects(PRODUCTS)

    assert result.field_coverage["title"]["products"] == 2
    assert result.field_coverage["gallery"]["products"] == 2
    assert result.field_coverage["gallery[].img"]["products"] == 1
    assert result.field_coverage["editions[].quantity"]["products"] == 2
    assert result.field_coverage["future_field.nested"]["products"] == 1


def test_empty_arrays_are_recorded_without_inventing_child_fields() -> None:
    result = explore_product_objects([{"uid": 1, "properties": []}])

    assert result.field_coverage["properties"]["products"] == 1
    assert "properties[]" not in result.field_coverage


def test_collects_named_characteristic_and_property_labels() -> None:
    result = explore_product_objects(PRODUCTS)

    assert result.catalog_statistics["characteristics"]["labels"] == {
        "Высота": 1,
        "Материал": 1,
    }
    assert result.catalog_statistics["properties"]["labels"] == {"Страна": 1}


def test_unknown_fields_are_preserved_in_schema_tree() -> None:
    result = explore_product_objects(PRODUCTS)
    nested = result.schema_tree["children"]["future_field"]["children"]["nested"]

    assert nested["products"] == 1
    assert nested["types"] == {"boolean": 1}


def test_writes_deterministic_artifact_set(tmp_path) -> None:
    result = explore_product_objects(PRODUCTS)
    paths = write_exploration_artifacts(result, tmp_path)

    assert set(paths) == {"field_coverage", "schema_tree", "catalog_statistics"}
    coverage = json.loads(paths["field_coverage"].read_text(encoding="utf-8"))
    assert coverage["uid"]["products"] == 2
