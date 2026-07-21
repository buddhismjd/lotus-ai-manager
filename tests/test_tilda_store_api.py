from backend.integrations import tilda_store_api


def test_build_request_url_contains_pagination_parameters() -> None:
    url = tilda_store_api.build_request_url(
        storepartuid="111",
        recid="222",
        slice_number=3,
        page_size=36,
    )

    assert "storepartuid=111" in url
    assert "recid=222" in url
    assert "slice=3" in url
    assert "size=36" in url
    assert "getallparts=true" in url


def test_parse_store_product_handles_known_fields() -> None:
    product = tilda_store_api.parse_store_product(
        {
            "uid": 260561911092,
            "title": "Статуя Ушнишавиджая",
            "sku": "Ushnishavidzhaya-23000",
            "descr": "<p>Статуя для домашнего алтаря.</p>",
            "price": "23000",
            "currency": "RUB",
            "url": (
                "/statui-svet-lotosa/"
                "tproduct/260561911092-statuya-ushnishavidzhaya"
            ),
        }
    )

    assert product.uid == "260561911092"
    assert product.title == "Статуя Ушнишавиджая"
    assert product.description == "Статуя для домашнего алтаря."
    assert product.sku == "Ushnishavidzhaya-23000"
    assert product.url.startswith("https://svet-lotosa.tilda.ws/")


def test_product_to_document_creates_chunks() -> None:
    product = tilda_store_api.parse_store_product(
        {
            "uid": "384940676312",
            "title": "Статуя Белой Тары",
            "descr": "Статуя Белой Тары для домашнего алтаря.",
            "price": "13000",
        }
    )

    document = tilda_store_api.product_to_document(product)

    assert document["id"] == "product-384940676312"
    assert document["type"] == "product"
    assert document["title"] == "Статуя Белой Тары"
    assert document["chunks"]
    assert document["source_type"] == "tilda_store_api"


def test_fetch_all_products_follows_nextslice(monkeypatch) -> None:
    responses = {
        1: {
            "total": 3,
            "nextslice": 2,
            "products": [
                {"uid": "1", "title": "Товар 1"},
                {"uid": "2", "title": "Товар 2"},
            ],
        },
        2: {
            "total": 3,
            "nextslice": None,
            "products": [
                {"uid": "3", "title": "Товар 3"},
            ],
        },
    }

    monkeypatch.setattr(
        tilda_store_api,
        "fetch_store_slice",
        lambda **kwargs: responses[kwargs["slice_number"]],
    )

    products, metadata = tilda_store_api.fetch_all_products(
        storepartuid="111",
        recid="222",
    )

    assert len(products) == 3
    assert metadata["expected_total"] == 3
    assert metadata["received_total"] == 3
    assert metadata["pages"] == 2


def test_parse_store_product_preserves_image_material_and_explicit_status() -> None:
    product = tilda_store_api.parse_store_product(
        {
            "uid": "900",
            "title": "Статуя Зеленой Тары",
            "descr": "Бронзовая статуя. Высота 14 см.",
            "img": "//static.tildacdn.com/statue.jpg",
            "availability_status": "Под заказ",
            "material": "бронза",
        }
    )

    assert product.image_url == "https://static.tildacdn.com/statue.jpg"
    assert product.material == "бронза"
    assert product.availability_status == "Под заказ"


def test_product_document_contains_commercial_card_metadata() -> None:
    product = tilda_store_api.parse_store_product(
        {
            "uid": "901",
            "title": "Статуя Будды",
            "descr": "Латунная статуя. Высота 12 см.",
            "img": "https://static.tildacdn.com/buddha.jpg",
            "availability": "В наличии",
        }
    )

    document = tilda_store_api.product_to_document(product)

    assert "Изображение: https://static.tildacdn.com/buddha.jpg" in document["content"]
    assert "Материал: латунь" in document["content"]
    assert "Статус: В наличии" in document["content"]
