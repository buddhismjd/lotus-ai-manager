from backend.knowledge.aspect_registry import (
    canonical_aspect_id,
    canonical_aspect_name,
    load_aspect_registry,
)


def test_new_aspects_are_loaded() -> None:
    registry = load_aspect_registry()

    expected = {
        "amitabha_buddha",
        "shakyamuni_buddha",
        "garuda",
        "manjushri",
        "mahakala",
        "ushnishavijaya",
    }

    assert expected.issubset(registry)


def test_amitabha_aliases() -> None:
    assert canonical_aspect_id("Будды Амитабхи") == "amitabha_buddha"
    assert canonical_aspect_name("Амитабха") == "Будда Амитабха"


def test_shakyamuni_aliases() -> None:
    assert canonical_aspect_id("Будде Шакьямуни") == "shakyamuni_buddha"


def test_protective_aspects_aliases() -> None:
    assert canonical_aspect_id("Махакалы") == "mahakala"
    assert canonical_aspect_id("Гаруде") == "garuda"


def test_wisdom_and_longevity_aliases() -> None:
    assert canonical_aspect_id("Манджушри") == "manjushri"
    assert canonical_aspect_id("Ушнишавиджаи") == "ushnishavijaya"
