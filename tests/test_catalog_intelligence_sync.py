from backend.integrations import catalog_intelligence_sync
from backend.integrations.tilda_store_api import StoreProduct


def test_build_product_profile_for_white_tara_statue() -> None:
    product = StoreProduct(
        uid="384940676312",
        title="Статуя Белой Тары",
        description=(
            "Латунная статуя для домашнего алтаря. "
            "Тибетский буддизм."
        ),
        price="13000",
        currency="RUB",
        sku="white-tara",
        url="https://example.com/white-tara",
        category="Статуи",
        image_url="",
        raw={"uid": "384940676312"},
    )

    profile = catalog_intelligence_sync.build_product_profile(product)

    assert profile.product_id == "product-384940676312"
    assert profile.product_type == "statue"
    assert profile.primary_entity == "Белая Тара"
    assert "латунь" in profile.materials
    assert "home_altar" in profile.usages
    assert "Ваджраяна" in profile.traditions
    assert "статуэтка" in profile.synonyms


def test_build_product_profile_for_vajra() -> None:
    product = StoreProduct(
        uid="2",
        title="Ваджра пятиконечная",
        description="Ритуальная ваджра для практики.",
        price="",
        currency="",
        sku="vajra",
        url="https://example.com/vajra",
        category="Ритуальные предметы",
        image_url="",
        raw={"uid": "2"},
    )

    profile = catalog_intelligence_sync.build_product_profile(product)

    assert profile.product_type == "vajra"
    assert "дордже" in profile.synonyms
    assert "practice" in profile.usages
