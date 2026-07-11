from backend.integrations import sqlite_product_crawler_sync as sync


def test_manual_white_tara_product_is_always_included() -> None:
    urls = sync.normalized_product_urls([])

    assert any(
        "384940676312-statuya-beloi-tari" in url
        for url in urls
    )


def test_product_urls_are_deduplicated_by_tilda_id() -> None:
    urls = sync.normalized_product_urls(
        [
            (
                "https://svet-lotosa.tilda.ws/a/"
                "tproduct/384940676312-statuya-beloi-tari"
            ),
            (
                "https://svet-lotosa.tilda.ws/statui-svet-lotosa/"
                "tproduct/384940676312-statuya-beloi-tari"
            ),
        ]
    )

    matching = [
        url
        for url in urls
        if "384940676312" in url
    ]

    assert len(matching) == 1


def test_page_to_document_builds_sqlite_product() -> None:
    document = sync.page_to_document(
        {
            "title": "Статуя Белой Тары",
            "text": "Статуя Белой Тары для домашнего алтаря.",
        },
        (
            "https://svet-lotosa.tilda.ws/statui-svet-lotosa/"
            "tproduct/384940676312-statuya-beloi-tari"
        ),
    )

    assert document["id"] == "product-384940676312"
    assert document["type"] == "product"
    assert document["title"] == "Статуя Белой Тары"
    assert document["enabled"] is True
    assert document["chunks"]


def test_short_product_content_still_creates_a_chunk() -> None:
    document = sync.page_to_document(
        {
            "title": "Статуя Белой Тары",
            "text": "Короткое описание.",
        },
        (
            "https://svet-lotosa.tilda.ws/statui-svet-lotosa/"
            "tproduct/384940676312-statuya-beloi-tari"
        ),
    )

    assert document["chunks"] == ["Короткое описание."]

