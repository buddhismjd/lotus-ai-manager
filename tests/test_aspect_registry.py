from types import SimpleNamespace

from backend.knowledge.aspect_migration import (
    canonicalize_profile_aspects,
)
from backend.knowledge.aspect_registry import (
    canonical_aspect_id,
    canonical_aspect_name,
    resolve_aspect,
)


def test_white_tara_case_forms_resolve() -> None:
    for value in (
        "Белая Тара",
        "Белой Таре",
        "Белую Тару",
        "White Tara",
        "Сита Тара",
    ):
        assert canonical_aspect_id(value) == "white_tara"
        assert canonical_aspect_name(value) == "Белая Тара"


def test_milarepa_case_forms_resolve() -> None:
    for value in (
        "Миларепа",
        "Миларепу",
        "Миларепе",
    ):
        assert canonical_aspect_id(value) == "milarepa"


def test_chenrezig_alias_resolves() -> None:
    assert canonical_aspect_id("Авалокитешвара") == "chenrezig"
    assert canonical_aspect_id("Ченрезига") == "chenrezig"


def test_profile_legacy_entities_are_canonicalized() -> None:
    profile = SimpleNamespace(
        entities=("Белой Таре", "Миларепе"),
    )

    result = canonicalize_profile_aspects(profile)

    assert [item.aspect_id for item in result] == [
        "white_tara",
        "milarepa",
    ]
