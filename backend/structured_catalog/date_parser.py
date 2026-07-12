from __future__ import annotations

import re

from backend.structured_catalog.models import TourSchedule

_MONTHS = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "мая": 5,
    "май": 5,
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
}
_MONTH_PATTERN = (
    r"январ[ья]|феврал[ья]|март[а]?|апрел[ья]|ма[йя]|июн[ья]|"
    r"июл[ья]|август[а]?|сентябр[ья]|октябр[ья]|ноябр[ья]|декабр[ья]"
)
_RANGE_WITH_TWO_MONTHS = re.compile(
    rf"(?P<start_day>\d{{1,2}})\s+(?P<start_month>{_MONTH_PATTERN})"
    rf"\s*[–—-]\s*(?P<end_day>\d{{1,2}})\s+(?P<end_month>{_MONTH_PATTERN})",
    re.IGNORECASE,
)
_RANGE_WITH_ONE_MONTH = re.compile(
    rf"(?P<start_day>\d{{1,2}})\s*[–—-]\s*(?P<end_day>\d{{1,2}})"
    rf"\s+(?P<month>{_MONTH_PATTERN})",
    re.IGNORECASE,
)
_DURATION_RE = re.compile(r"\b(?P<days>\d{1,3})\s*(?:дней|дня|день)\b", re.IGNORECASE)


def _month_number(value: str) -> int | None:
    normalized = value.casefold().replace("ё", "е")
    for prefix, number in _MONTHS.items():
        if normalized.startswith(prefix):
            return number
    return None


def parse_tour_schedule(text: str) -> TourSchedule | None:
    normalized = text.replace("\xa0", " ")
    match = _RANGE_WITH_TWO_MONTHS.search(normalized)
    if match:
        start_month = _month_number(match.group("start_month"))
        end_month = _month_number(match.group("end_month"))
        if start_month and end_month:
            return TourSchedule(
                start_day=int(match.group("start_day")),
                start_month=start_month,
                end_day=int(match.group("end_day")),
                end_month=end_month,
                source_text=" ".join(match.group(0).split()),
            )

    match = _RANGE_WITH_ONE_MONTH.search(normalized)
    if match:
        month = _month_number(match.group("month"))
        if month:
            return TourSchedule(
                start_day=int(match.group("start_day")),
                start_month=month,
                end_day=int(match.group("end_day")),
                end_month=month,
                source_text=" ".join(match.group(0).split()),
            )
    return None


def parse_duration_days(title: str, description: str) -> int | None:
    for value in (title, description):
        match = _DURATION_RE.search(value.replace("\xa0", " "))
        if match:
            return int(match.group("days"))
    return None
