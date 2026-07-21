from __future__ import annotations

from decimal import Decimal

import pytest

from backend.integrations.product_raw_snapshot import (
    build_raw_snapshot,
    extract_product_object,
)
from backend.integrations.product_snapshot_normalizer import (
    normalize_raw_snapshot,
)


HTML = """
<html><script>
var product = {
  "uid":296122659532,
  "title":"Ваджра",
  "brand":"Тибет",
  "text":"Описание <br> товара",
  "sku":"Vadzhra-25000",
  "price":"25000.0000",
  "gallery":[
    {"img":"https://static.test/one.jpg"},
    {"img":"https://static.test/two.jpg"}
  ],
  "quantity":"0",
  "characteristics":[],
  "properties":[],
  "partuids":[287310077602],
  "url":"https://example.test/tproduct/296122659532-vadzhra"
};
</script></html>
"""


def test_extracts_confirmed_tilda_product_object() -> None:
    data, raw_json = extract_product_object(HTML)
    assert data["uid"] == 296122659532
    assert data["price"] == "25000.0000"
    assert '"gallery"' in raw_json


def test_normalizes_only_confirmed_fields() -> None:
    item = normalize_raw_snapshot(
        build_raw_snapshot(
            HTML,
            "https://example.test/tproduct/296122659532-vadzhra",
        )
    )
    assert item.title == "Ваджра"
    assert item.price == Decimal("25000.0000")
    assert item.primary_image == "https://static.test/one.jpg"
    assert item.gallery == (
        "https://static.test/one.jpg",
        "https://static.test/two.jpg",
    )
    assert item.quantity == Decimal("0")
    assert item.category is None
    assert item.material is None
    assert item.height_cm is None
    assert item.availability_status is None


def test_raw_snapshot_is_deterministic() -> None:
    first = build_raw_snapshot(HTML, "https://example.test/product")
    second = build_raw_snapshot(HTML, "https://example.test/product")
    assert first.snapshot_sha256 == second.snapshot_sha256
    assert first.html_sha256 == second.html_sha256


def test_missing_product_object_fails_explicitly() -> None:
    with pytest.raises(ValueError, match="var product"):
        extract_product_object("<html></html>")
