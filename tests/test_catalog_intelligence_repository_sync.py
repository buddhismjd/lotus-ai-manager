from types import SimpleNamespace

from backend.integrations.catalog_intelligence_repository_sync import (
    build_repository_product_profile,
)


def product(
    title: str,
    category: str,
    description: str,
    url: str,
):
    return SimpleNamespace(
        title=title,
        category=category,
        description=description,
        url=url,
        material="",
        keywords=[],
        sku="",
    )


def test_statue_profile_uses_tilda_uid() -> None:
    profile = build_repository_product_profile(
        product(
            "Статуя Белой Тары",
            "Статуи",
            "Латунная статуя для домашнего алтаря.",
            (
                "https://svet-lotosa.tilda.ws/statui-svet-lotosa/"
                "tproduct/384940676312-statuya-beloi-tari"
            ),
        )
    )

    assert profile.product_id == "product-384940676312"
    assert profile.product_type == "statue"
    assert profile.primary_entity == "Белая Тара"


def test_earrings_with_dorje_remain_jewelry() -> None:
    profile = build_repository_product_profile(
        product(
            "Серебряные серьги",
            "Серьги",
            "Украшены символом двойного дордже.",
            (
                "https://svet-lotosa.tilda.ws/sergi-svet-lotosa/"
                "tproduct/694310450132-serebryanie-sergi"
            ),
        )
    )

    assert profile.product_type == "jewelry"


def test_mala_profile_is_not_statue() -> None:
    profile = build_repository_product_profile(
        product(
            "Коралловые чётки",
            "Малы (четки)",
            "Мала для ежедневной практики.",
            (
                "https://svet-lotosa.tilda.ws/chetki-svet-lotosa/"
                "tproduct/123456789012-korallovie-chetki"
            ),
        )
    )

    assert profile.product_type == "mala"


def test_gau_profile_is_amulet_not_vajra() -> None:
    profile = build_repository_product_profile(
        product(
            "Серебряное гау с двойным дордже",
            "Гау",
            "Амулет-гау с символом двойного дордже.",
            (
                "https://svet-lotosa.tilda.ws/gau-svet-lotosa/"
                "tproduct/123456789013-gau-dordje"
            ),
        )
    )

    assert profile.product_type == "amulet"
