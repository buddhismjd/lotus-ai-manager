from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product


def test_specific_pendant_query_does_not_return_whole_category(monkeypatch):
    monkeypatch.setattr(
        "backend.catalog.collection_builder.get_product_profile",
        lambda _product_id: None,
    )
    products = [
        Product(
            id="knot-small",
            title='Серебряная подвеска "Бесконечный узел"',
            url="https://example.test/tproduct/1",
            category="Подвески",
        ),
        Product(
            id="dorje",
            title='Серебряная подвеска "Дордже"',
            url="https://example.test/tproduct/2",
            category="Подвески",
        ),
        Product(
            id="symbols",
            title='Серебряная подвеска "8 благоприятных символов"',
            url="https://example.test/tproduct/3",
            category="Подвески",
        ),
    ]

    items = build_product_collection("Подвеска с бесконечным узлом есть?", products)

    assert [item.id for item in items] == ["knot-small"]


def test_specific_bell_query_does_not_fall_back_to_vajra(monkeypatch):
    monkeypatch.setattr(
        "backend.catalog.collection_builder.get_product_profile",
        lambda _product_id: None,
    )
    products = [
        Product(
            id="vajra",
            title="Ваджра",
            url="https://example.test/tproduct/1",
        ),
        Product(
            id="bell-vajra",
            title="Колокольчик Ганта с ваджрой",
            url="https://example.test/tproduct/2",
        ),
    ]

    items = build_product_collection("Колокольчик с ваджрой есть?", products)

    assert [item.id for item in items] == ["bell-vajra"]


def test_missing_stock_is_loaded_from_exact_product_page(monkeypatch):
    monkeypatch.setattr(
        "backend.catalog.collection_builder.get_product_profile",
        lambda _product_id: None,
    )

    class Snapshot:
        availability_status = "Под заказ"

    seen = []

    def fake_snapshot(url, timeout):
        seen.append((url, timeout))
        return Snapshot()

    monkeypatch.setattr(
        "backend.catalog.collection_builder.load_product_page_snapshot",
        fake_snapshot,
    )
    product = Product(
        id="knot",
        title='Серебряная подвеска "Бесконечный узел"',
        url=(
            "https://svet-lotosa.tilda.ws/podveski-svet-lotosa/"
            "tproduct/1-beskonechnii-uzel"
        ),
        category="Подвески",
    )

    items = build_product_collection("Подвеска с бесконечным узлом", [product])

    assert len(items) == 1
    assert items[0].availability == "Под заказ"
    assert items[0].group == "Под заказ"
    assert seen == [(product.url, 12.0)]
