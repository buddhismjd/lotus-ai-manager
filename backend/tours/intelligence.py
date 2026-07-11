from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from backend.tours.profiles import TourProfile


COUNTRY_PATTERNS = {
    "Непал": (
        "непал",
        "катманду",
        "лапчи",
        "мустанг",
    ),
    "Тибет": (
        "тибет",
        "лхаса",
        "кайлас",
    ),
    "Индия": (
        "инди",
        "дхарамсала",
        "бодхгая",
        "ладакх",
        "ладкх",
        "занскар",
        "маркха",
        "марха",
        "куллу",
        "кулу",
    ),
    "Бутан": (
        "бутан",
        "тхимпху",
        "паро",
    ),
    "Монголия": (
        "монгол",
    ),
    "Россия": (
        "росси",
        "алтай",
        "белух",
    ),
}


REGION_PATTERNS = {
    "Лапчи": ("лапчи", "lapchi"),
    "Кайлас": ("кайлас", "kailash"),
    "Мустанг": ("мустанг", "mustang"),
    "Катманду": ("катманду", "kathmandu"),
    "Тибет": ("тибет",),
    "Алтай": ("алтай", "altay", "altai"),
    "Белуха": ("белух", "belukha"),
    "Ладакх": ("ладакх", "ладкх", "ladakh"),
    "Занскар": ("занскар", "zanskar"),
    "Долина Куллу": (
        "долина куллу",
        "куллу",
        "кулу",
        "kullu",
    ),
    "Долина Маркха": (
        "долина маркха",
        "долина марха",
        "маркха",
        "марха",
        "markha",
    ),
}


DESTINATION_PATTERNS = {
    "Лапчи": ("лапчи",),
    "Кайлас": ("кайлас",),
    "Миларепа": ("милареп",),
    "Катманду": ("катманду",),
    "Лхаса": ("лхаса",),
    "Алтай": ("алтай",),
    "Белуха": ("белух",),
    "Ладакх": ("ладакх", "ладкх"),
    "Занскар": ("занскар",),
    "Долина Куллу": ("долина куллу", "куллу", "кулу"),
    "Долина Маркха": (
        "долина маркха",
        "долина марха",
        "маркха",
        "марха",
    ),
}


ASPECT_PATTERNS = {
    "Миларепа": ("милареп",),
    "Гуру Ринпоче": ("гуру ринпоче", "падмасамбхав"),
    "Ченрезиг": ("ченрезиг", "авалокит"),
}

PRACTICE_PATTERNS = {
    "кора": ("кора", "обход"),
    "паломничество": ("паломнич",),
    "медитация": ("медитац",),
    "ретрит": ("ретрит",),
    "поход": ("поход", "треккинг", "трекинг"),
}

TEACHER_PATTERNS = {
    "Миларепа": ("милареп",),
    "Гуру Ринпоче": ("гуру ринпоче", "падмасамбхав"),
}

DIFFICULTY_PATTERNS = {
    "лёгкая": ("легк", "лёгк"),
    "средняя": ("средн",),
    "сложная": ("сложн", "тяжел", "тяжёл"),
}

DURATION_RE = re.compile(
    r"""
    (?<!\d)
    (?P<days>\d{1,3})
    \s*
    (?:[-–—]\s*)?
    (?:
        дневн[а-я]*
        |
        дн(?:я|ей)?
        |
        день
    )
    \b
    """,
    re.IGNORECASE | re.VERBOSE,
)


ALTITUDE_RE = re.compile(
    r"(?<!\d)(\d{3,5})\s*(?:м|метр(?:а|ов)?)\b",
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    return (
        (text or "")
        .lower()
        .replace("ё", "е")
    )


def _detect(
    text: str,
    patterns: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    normalized = normalize(text)

    return tuple(
        label
        for label, aliases in patterns.items()
        if any(normalize(alias) in normalized for alias in aliases)
    )


def _duration_days(text: str) -> int | None:
    values = [
        int(match.group("days"))
        for match in DURATION_RE.finditer(text or "")
    ]

    if not values:
        return None

    return max(values)


def _altitude_range(text: str) -> tuple[int | None, int | None]:
    values = [
        int(match.group(1))
        for match in ALTITUDE_RE.finditer(text or "")
    ]

    if not values:
        return None, None

    return min(values), max(values)


def _tour_id(tour: Any) -> str:
    source_id = str(
        getattr(tour, "source_id", "")
        or getattr(tour, "id", "")
        or ""
    ).strip()

    if source_id:
        return (
            source_id
            if source_id.startswith("tour-")
            else f"tour-{source_id}"
        )

    stable_source = "|".join(
        [
            str(getattr(tour, "title", "") or ""),
            str(getattr(tour, "url", "") or ""),
        ]
    )
    digest = hashlib.sha256(
        stable_source.encode("utf-8")
    ).hexdigest()[:20]
    return f"tour-local-{digest}"


def build_tour_profile(tour: Any) -> TourProfile:
    title = str(getattr(tour, "title", "") or "")
    description = str(getattr(tour, "description", "") or "")
    country = str(getattr(tour, "country", "") or "")
    region = str(getattr(tour, "region", "") or "")
    difficulty = str(getattr(tour, "difficulty", "") or "")
    guide = str(getattr(tour, "guide", "") or "")
    keywords = tuple(
        str(value)
        for value in (getattr(tour, "keywords", []) or [])
        if str(value).strip()
    )

    url = str(getattr(tour, "url", "") or "")
    text = " ".join(
        [
            title,
            description,
            country,
            region,
            difficulty,
            guide,
            url,
            *keywords,
        ]
    )

    countries = tuple(dict.fromkeys(
        [
            *([country] if country else []),
            *_detect(text, COUNTRY_PATTERNS),
        ]
    ))
    regions = tuple(dict.fromkeys(
        [
            *([region] if region else []),
            *_detect(text, REGION_PATTERNS),
        ]
    ))
    destinations = _detect(text, DESTINATION_PATTERNS)
    aspects = _detect(text, ASPECT_PATTERNS)
    practices = _detect(text, PRACTICE_PATTERNS)
    teachers = tuple(dict.fromkeys(
        [
            *([guide] if guide else []),
            *_detect(text, TEACHER_PATTERNS),
        ]
    ))

    detected_difficulty = difficulty or next(
        iter(_detect(text, DIFFICULTY_PATTERNS)),
        None,
    )
    min_altitude, max_altitude = _altitude_range(text)

    source_payload = {
        "title": title,
        "description": description,
        "country": country,
        "region": region,
        "difficulty": difficulty,
        "guide": guide,
        "keywords": keywords,
        "url": url,
    }

    return TourProfile(
        tour_id=_tour_id(tour),
        countries=countries,
        regions=regions,
        destinations=destinations,
        aspects=aspects,
        practices=practices,
        teachers=teachers,
        difficulty=detected_difficulty,
        duration_days=_duration_days(text),
        min_altitude_m=min_altitude,
        max_altitude_m=max_altitude,
        keywords=tuple(dict.fromkeys([
            *keywords,
            *countries,
            *regions,
            *destinations,
            *aspects,
            *practices,
            *teachers,
        ])),
        source_hash=hashlib.sha256(
            json.dumps(
                source_payload,
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest(),
    )


__all__ = [
    "build_tour_profile",
]
