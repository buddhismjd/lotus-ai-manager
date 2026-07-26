from __future__ import annotations

import re
from dataclasses import dataclass


CYRILLIC_HOMOGLYPHS = str.maketrans(
    {
        "c": "с",
        "a": "а",
        "e": "е",
        "o": "о",
        "p": "р",
        "x": "х",
        "y": "у",
        "k": "к",
        "m": "м",
        "t": "т",
        "b": "в",
        "h": "н",
    }
)


def _repair_mixed_script_words(value: str) -> str:
    words = value.split()
    repaired: list[str] = []

    for word in words:
        has_cyrillic = bool(re.search(r"[а-яё]", word))
        has_latin = bool(re.search(r"[a-z]", word))

        if has_cyrillic and has_latin:
            word = word.translate(CYRILLIC_HOMOGLYPHS)

        repaired.append(word)

    return " ".join(repaired)


def normalize(text: str) -> str:
    value = (text or "").lower().replace("ё", "е")
    value = _repair_mixed_script_words(value)
    value = re.sub(r"[^a-zа-я0-9\s-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


# Product type must primarily come from title/category. Description is only
# a fallback because it may mention related ritual symbols and create false
# classifications, e.g. earrings with a dorje should remain jewelry.
TITLE_TYPE_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("statue", ("стату", "статует", "скульптур")),
    ("thangka", ("тханк", "танка")),
    ("singing_bowl", ("поющ чаш", "тибетск чаш")),
    ("jewelry", ("серьг", "кольц", "браслет", "ожерел")),
    ("amulet", ("амулет", "подвес", "кулон", "медальон", "мелонг", "гау", "цаца")),
    ("mala", ("четк", "мала")),
    ("vajra", ("ваджр",)),
    ("bell", ("колоколь", "гант", "гхант")),
    ("incense", ("благовон", "аромапал")),
    (
        "ritual_item",
        (
            "бумп",
            "дигуг",
            "картик",
            "пхурб",
            "наклейк",
            "защитн наклейк",
            "бутанск пенис",
        ),
    ),
)

DESCRIPTION_FALLBACK_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("statue", ("стату", "скульптур")),
    ("thangka", ("тханк", "буддийск танка")),
    ("singing_bowl", ("поющ чаш",)),
    ("amulet", ("амулет", "оберег")),
    ("mala", ("четк", "мала")),
    ("vajra", ("ритуальн ваджр", "пятиконечн ваджр")),
    ("bell", ("колоколь", "ритуальн гант", "ритуальн гхант")),
    ("incense", ("благовон",)),
)

ENTITY_PATTERNS: dict[str, tuple[str, ...]] = {
    "Белая Тара": ("белая тара", "белой тары", "белую тару"),
    "Зелёная Тара": ("зеленая тара", "зеленой тары", "зеленую тару"),
    "Будда Шакьямуни": ("будда шакьямуни", "шакьямуни"),
    "Будда Амитабха": ("будда амитабх", "амитабх"),
    "Будда Медицины": ("будда медицин",),
    "Будда": ("будда", "буддой"),
    "Ченрезиг": ("ченрезиг", "авалокитешвар"),
    "Манджушри": ("манджушр", "манчжушр"),
    "Гуру Ринпоче": ("гуру ринпоче", "падмасамбхав"),
    "Ваджрасаттва": ("ваджрасаттв",),
    "Миларепа": ("милареп",),
    "Дзамбала": ("дзамбал",),
    "Махакала": ("махакал",),
    "Ушнишавиджая": ("ушнишавиджа",),
    "Гаруда": ("гаруд",),
}

MATERIAL_PATTERNS: dict[str, tuple[str, ...]] = {
    "серебро": ("серебр",),
    "латунь": ("латун",),
    "бронза": ("бронз",),
    "медь": ("медн", "медь"),
    "дерево": ("дерев",),
    "обсидиан": ("обсидиан",),
    "полистоун": ("полистоун",),
    "камень": ("камен", "камень"),
    "кость": ("костян", "кость"),
}

USAGE_PATTERNS: dict[str, tuple[str, ...]] = {
    "protection": ("защит", "оберег", "охраня", "устраняет препятств"),
    "home_altar": ("домашн алтар", "для алтар", "алтарн"),
    "meditation": ("медитац",),
    "practice": ("практик", "ритуальн"),
    "gift": ("подар",),
    "prosperity": ("богатств", "процветан", "изобил"),
    "healing": ("исцелен", "здоров", "долголет"),
}

USAGE_LABELS = {
    "protection": "защита",
    "home_altar": "домашний алтарь",
    "meditation": "медитация",
    "practice": "практика",
    "gift": "подарок",
    "prosperity": "процветание",
    "healing": "исцеление",
}

TYPE_SYNONYMS = {
    "statue": ("статуя", "статуэтка", "скульптура"),
    "thangka": ("тханка", "танка"),
    "singing_bowl": ("поющая чаша", "тибетская чаша"),
    "jewelry": ("украшение",),
    "amulet": ("амулет", "подвеска", "кулон", "гау", "цаца"),
    "mala": ("чётки", "четки", "мала"),
    "vajra": ("ваджра", "дордже"),
    "bell": ("колокольчик", "ганта", "гханта"),
    "incense": ("благовония",),
    "ritual_item": ("ритуальный предмет",),
}


@dataclass(frozen=True, slots=True)
class ProductIntelligence:
    product_type: str | None = None
    entities: tuple[str, ...] = ()
    materials: tuple[str, ...] = ()
    usages: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    synonyms: tuple[str, ...] = ()

    def to_search_text(self) -> str:
        parts: list[str] = []

        if self.product_type:
            parts.append(f"Тип товара: {self.product_type}")
        if self.entities:
            parts.append("Сущности: " + ", ".join(self.entities))
        if self.materials:
            parts.append("Материалы: " + ", ".join(self.materials))
        if self.usages:
            labels = [USAGE_LABELS.get(value, value) for value in self.usages]
            parts.append("Назначение: " + ", ".join(labels))
        if self.synonyms:
            parts.append("Синонимы: " + ", ".join(self.synonyms))
        if self.keywords:
            parts.append("Ключевые слова: " + ", ".join(self.keywords))

        return "\n".join(parts)


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    normalized_text = normalize(text)
    words = normalized_text.split()

    for pattern in patterns:
        roots = normalize(pattern).split()
        if not roots:
            continue

        if len(roots) == 1:
            if any(word.startswith(roots[0]) for word in words):
                return True
            continue

        width = len(roots)
        for index in range(len(words) - width + 1):
            window = words[index : index + width]
            if all(word.startswith(root) for word, root in zip(window, roots)):
                return True

    return False


def _detect_type(title: str, category: str, description: str) -> str | None:
    primary_text = " ".join(part for part in [title, category] if part)

    for product_type, patterns in TITLE_TYPE_PATTERNS:
        if _matches(primary_text, patterns):
            return product_type

    for product_type, patterns in DESCRIPTION_FALLBACK_PATTERNS:
        if _matches(description, patterns):
            return product_type

    return None


def analyze_product(
    *,
    title: str,
    description: str = "",
    category: str = "",
    sku: str = "",
) -> ProductIntelligence:
    product_type = _detect_type(title, category, description)
    full_text = normalize(" ".join([title, description, category, sku]))

    entities = tuple(
        entity
        for entity, patterns in ENTITY_PATTERNS.items()
        if _matches(full_text, patterns)
    )

    # Avoid adding generic "Будда" when a more specific Buddha entity exists.
    if any(entity.startswith("Будда ") for entity in entities):
        entities = tuple(entity for entity in entities if entity != "Будда")

    materials = tuple(
        material
        for material, patterns in MATERIAL_PATTERNS.items()
        if _matches(full_text, patterns)
    )

    usages = tuple(
        usage
        for usage, patterns in USAGE_PATTERNS.items()
        if _matches(full_text, patterns)
    )

    synonyms = TYPE_SYNONYMS.get(product_type, ())

    keywords: list[str] = []
    if product_type:
        keywords.append(product_type)
    keywords.extend(entities)
    keywords.extend(materials)
    keywords.extend(usages)
    keywords.extend(synonyms)

    return ProductIntelligence(
        product_type=product_type,
        entities=entities,
        materials=materials,
        usages=usages,
        keywords=tuple(dict.fromkeys(keywords)),
        synonyms=tuple(dict.fromkeys(synonyms)),
    )


__all__ = ["ProductIntelligence", "analyze_product"]
