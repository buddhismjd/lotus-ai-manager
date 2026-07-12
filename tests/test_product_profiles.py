from backend.catalog.product_profiles import ProductProfile


def test_profile_search_text_contains_structured_fields() -> None:
    profile = ProductProfile(
        product_id="product-1",
        product_type="statue",
        primary_entity="Белая Тара",
        entities=("Белая Тара",),
        materials=("латунь",),
        usages=("home_altar",),
        traditions=("Ваджраяна",),
        synonyms=("статуя", "статуэтка"),
        keywords=("тара", "алтарь"),
    )

    text = profile.to_search_text()

    assert "Тип товара: statue" in text
    assert "Основной аспект: Белая Тара" in text
    assert "Материалы: латунь" in text
    assert "Назначение: home_altar" in text
    assert "Традиции: Ваджраяна" in text
