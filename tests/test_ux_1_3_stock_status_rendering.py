from dataclasses import replace

from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product
from backend.integrations.tilda_store_api import _extract_availability_status


def test_generic_payload_label_does_not_create_false_in_stock():
    product = {"title": "Статуя", "html": "Кнопка фильтра: В наличии"}
    assert _extract_availability_status(product) is None


def test_zero_quantity_means_out_of_stock():
    assert _extract_availability_status({"title": "Статуя", "quantity": 0}) == "Нет в наличии"


def test_out_of_stock_has_own_collection_group():
    items = build_product_collection("статуя Ямантаки", [Product(
        id="1", title="Статуя Ямантаки", url="https://example.test/1",
        availability_status="Нет в наличии",
    )])
    assert items[0].availability == "Нет в наличии"
    assert items[0].group == "Нет в наличии"
