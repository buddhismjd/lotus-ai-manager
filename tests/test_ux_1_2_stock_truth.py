from __future__ import annotations

from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product


def test_unknown_stock_is_not_presented_as_in_stock(monkeypatch):
    monkeypatch.setattr(
        "backend.catalog.collection_builder.get_product_profile",
        lambda _product_id: None,
    )
    product = Product(
        id="green-tara",
        title="Статуя Зелёной Тары",
        url="https://example.test/tproduct/1",
        availability_status=None,
        available=True,  # legacy publication flag must not be treated as stock
    )

    item = build_product_collection("статуя Зелёной Тары", [product])[0]

    assert item.availability is None
    assert item.group == "Наличие уточняется"


def test_explicit_stock_status_is_preserved(monkeypatch):
    monkeypatch.setattr(
        "backend.catalog.collection_builder.get_product_profile",
        lambda _product_id: None,
    )
    product = Product(
        id="white-tara",
        title="Статуя Белой Тары",
        url="https://example.test/tproduct/2",
        availability_status="В наличии",
    )

    item = build_product_collection("статуя Белой Тары", [product])[0]

    assert item.availability == "В наличии"
    assert item.group == "В наличии"
