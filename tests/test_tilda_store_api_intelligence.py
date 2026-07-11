from backend.integrations import tilda_store_api


def test_document_contains_product_intelligence() -> None:
    product = tilda_store_api.parse_store_product(
        {
            "uid": "384940676312",
            "title": "Статуя Белой Тары",
            "descr": "Латунная статуя Белой Тары для домашнего алтаря.",
            "price": "13000",
        }
    )

    document = tilda_store_api.product_to_document(product)

    assert "Тип товара: statue" in document["content"]
    assert "Сущности: Белая Тара" in document["content"]
    assert "Материалы: латунь" in document["content"]
    assert "Назначение: домашний алтарь" in document["content"]
