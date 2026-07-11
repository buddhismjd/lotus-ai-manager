from __future__ import annotations

import re
from dataclasses import dataclass


def normalize(text: str) -> str:
    value = (text or "").lower().replace("ё", "е")
    value = re.sub(r"[^a-zа-я0-9\s-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


PRODUCT_TYPE_PATTERNS: dict[str, tuple[str, ...]] = {
    "statue": ("статуя", "статуэтка", "скульптура"),
    "thangka": ("тханка", "танка буддийская"),
    "singing_bowl": ("поющая чаша", "поющие чаши", "тибетская чаша"),
    "amulet": (
        "амулет", "подвеска", "кулон", "медальон",
        "мелонг", "гау", "цаца",
    ),
    "mala": ("четки", "чётки", "мала"),
    "vajra": ("ваджра", "дордже"),
    "incense": ("благовония", "благовоние", "аромапалочки"),
    "jewelry": ("браслет", "кольцо", "серьги", "ожерелье"),
    "ritual_item": ("бумпа", "дигуг", "картика", "пхурба"),
}

ENTITY_PATTERNS: dict[str, tuple[str, ...]] = {
    "Белая Тара": ("белая тара", "белой тары", "белую тару"),
    "Зелёная Тара": ("зеленая тара", "зеленой тары", "зеленую тару"),
    "Будда Шакьямуни": ("будда шакьямуни", "шакьямуни"),
    "Будда": ("будда", "буддой"),
    "Ченрезиг": ("ченрезиг", "авалокитешвара"),
    "Манджушри": ("манджушри", "манчжушри"),
    "Гуру Ринпоче": ("гуру ринпоче", "падмасамбхава"),
    "Ваджрасаттва": ("ваджрасаттва",),
    "Миларепа": ("миларепа",),
    "Дзамбала": ("дзамбала",),
    "Махакала": ("махакала",),
    "Ушнишавиджая": ("ушнишавиджая",),
    "Гаруда": ("гаруда",),
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
    "protection": ("защит", "оберег", "охраня", "устраняет препятствия"),
    "home_altar": ("домашн алтар", "для алтар", "алтарн"),
    "meditation": ("медитац", "для медитац"),
    "practice": ("практик", "ритуальн"),
    "gift": ("подар", "в подарок"),
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


@dataclass(frozen=True, slots=True)
class ProductIntelligence:
    product_type: str | None = None
    entities: tuple[str, ...] = ()
    materials: tuple[str, ...] = ()
    usages: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()

    def to_search_text(self) -> str:
        parts: list[str] = []

        if self.product_type:
            parts.append(f"Тип товара: {self.product_type}")
        if self.entities:
            parts.append("Сущности: " + ", ".join(self.entities))
        if self.materials:
            parts.append("Материалы: " + ", ".join(self.materials))
        if self.usages:
            usage_values = [USAGE_LABELS.get(usage, usage) for usage in self.usages]
            parts.append("Назначение: " + ", ".join(usage_values))
        if self.keywords:
            parts.append("Ключевые слова: " + ", ".join(self.keywords))

        return "\n".join(parts)


def _matches(text: str, aliases: tuple[str, ...]) -> bool:
    normalized_text = normalize(text)
    words = normalized_text.split()
    for alias in aliases:
        alias_words = normalize(alias).split()
        if not alias_words:
            continue
        if len(alias_words) == 1:
            root = alias_words[0]
            if any(word.startswith(root) for word in words):
                return True
            continue
        width = len(alias_words)
        for index in range(len(words) - width + 1):
            window = words[index:index + width]
            if all(word.startswith(root) for word, root in zip(window, alias_words)):
                return True
    return False


def analyze_product(
    *,
    title: str,
    description: str = "",
    category: str = "",
    sku: str = "",
) -> ProductIntelligence:
    text = normalize(" ".join([title, description, category, sku]))

    product_type = next(
        (
            kind
            for kind, aliases in PRODUCT_TYPE_PATTERNS.items()
            if _matches(text, aliases)
        ),
        None,
    )

    entities = tuple(
        entity
        for entity, aliases in ENTITY_PATTERNS.items()
        if _matches(text, aliases)
    )

    materials = tuple(
        material
        for material, aliases in MATERIAL_PATTERNS.items()
        if _matches(text, aliases)
    )

    usages = tuple(
        usage
        for usage, aliases in USAGE_PATTERNS.items()
        if _matches(text, aliases)
    )

    generated_keywords: list[str] = []
    if product_type:
        generated_keywords.append(product_type)
    generated_keywords.extend(entities)
    generated_keywords.extend(materials)
    generated_keywords.extend(usages)

    return ProductIntelligence(
        product_type=product_type,
        entities=entities,
        materials=materials,
        usages=usages,
        keywords=tuple(dict.fromkeys(generated_keywords)),
    )


__all__ = ["ProductIntelligence", "analyze_product"]
