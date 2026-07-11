from __future__ import annotations

import re


CYRILLIC_HOMOGLYPHS = str.maketrans(
    {
        "a": "а",
        "b": "в",
        "c": "с",
        "e": "е",
        "h": "н",
        "k": "к",
        "m": "м",
        "o": "о",
        "p": "р",
        "t": "т",
        "x": "х",
        "y": "у",
    }
)


def repair_mixed_script_words(value: str) -> str:
    """
    Repair visually identical Latin letters inside otherwise Cyrillic words.

    Example:
        Cтатуя -> Статуя
    """
    repaired: list[str] = []

    for word in (value or "").split():
        has_cyrillic = bool(re.search(r"[а-яё]", word, re.IGNORECASE))
        has_latin = bool(re.search(r"[a-z]", word, re.IGNORECASE))

        if has_cyrillic and has_latin:
            word = word.translate(CYRILLIC_HOMOGLYPHS)

        repaired.append(word)

    return " ".join(repaired)


def normalize_search_text(value: str | None) -> str:
    text = (value or "").lower().replace("ё", "е")
    text = repair_mixed_script_words(text)
    text = re.sub(r"[^a-zа-я0-9\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalized_contains(
    expected_fragment: str | None,
    actual_value: str | None,
) -> bool:
    expected = normalize_search_text(expected_fragment)
    actual = normalize_search_text(actual_value)

    if not expected:
        return True

    return expected in actual


__all__ = [
    "normalize_search_text",
    "normalized_contains",
    "repair_mixed_script_words",
]
