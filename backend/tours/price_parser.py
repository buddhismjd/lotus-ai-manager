from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class ParsedTourPrice:
    amount: Decimal
    currency: str
    source_text: str
    is_from: bool = False


_CURRENCY_ALIASES = {
    "₽": "RUR",
    "руб": "RUR",
    "руб.": "RUR",
    "рублей": "RUR",
    "рубля": "RUR",
    "rur": "RUR",
    "rub": "RUR",
    "$": "USD",
    "usd": "USD",
    "доллар": "USD",
    "доллара": "USD",
    "долларов": "USD",
    "€": "EUR",
    "eur": "EUR",
    "евро": "EUR",
}

_CURRENCY_TOKEN = r"(?:₽|руб(?:\.|лей|ля)?|RUR|RUB|\$|USD|доллар(?:а|ов)?|€|EUR|евро)"
_AMOUNT_TOKEN = (
    r"(?P<amount>"
    r"(?:\d{1,3}(?:[\s\u00a0,.]\d{3})+|\d{3,7})"
    r")(?:[.,](?P<fraction>\d{1,2}))?"
)

# A label is required for bare currency codes/words so dates and route numbers are
# not mistaken for prices. Currency symbols remain accepted without a label.
_PRICE_PATTERNS = (
    re.compile(
        rf"(?P<source>(?P<from>от\s+)?(?:стоимость|цена|участие|взнос|оплата)(?:\s+(?:тура|поездки|путешествия|программы))?\s*[:—–-]?\s*{_AMOUNT_TOKEN}\s*(?P<currency>{_CURRENCY_TOKEN}))",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<source>(?P<from>от\s+)?(?:стоимость|цена|участие|взнос|оплата)(?:\s+(?:тура|поездки|путешествия|программы))?\s*[:—–-]?\s*(?P<currency>{_CURRENCY_TOKEN})\s*{_AMOUNT_TOKEN})",
        re.IGNORECASE,
    ),
    # Tilda tour headers use a compact public-price line such as
    # ``от $ 1,450``. Requiring the leading ``от`` keeps arbitrary dollar
    # amounts in route details from being treated as the tour price.
    re.compile(
        rf"(?P<source>(?P<from>от\s+)(?P<currency>{_CURRENCY_TOKEN})\s*{_AMOUNT_TOKEN})",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<source>(?P<from>от\s+){_AMOUNT_TOKEN}\s*(?P<currency>{_CURRENCY_TOKEN}))",
        re.IGNORECASE,
    ),
)

def _currency(value: str) -> str:
    normalized = value.strip().casefold()
    return _CURRENCY_ALIASES.get(normalized, value.strip().upper())


def _amount(match: re.Match[str]) -> Decimal | None:
    whole = re.sub(r"[\s\u00a0,.]", "", match.group("amount"))
    fraction = match.groupdict().get("fraction")
    raw = f"{whole}.{fraction}" if fraction else whole
    try:
        amount = Decimal(raw)
    except (InvalidOperation, ValueError):
        return None
    return amount if amount > 0 else None


def parse_tour_price(text: str | None) -> ParsedTourPrice | None:
    """Extract one explicit public tour price from source page text.

    A price label (for example ``Стоимость тура`` or ``Цена``) is required.
    This prevents paid supplements, airfares and phrases such as
    ``В стоимость входит`` from being mistaken for the main tour price.
    """
    if not text:
        return None

    candidates: list[tuple[int, re.Match[str]]] = []
    for pattern in _PRICE_PATTERNS:
        candidates.extend((match.start(), match) for match in pattern.finditer(text))
    if not candidates:
        return None

    _, match = min(candidates, key=lambda item: item[0])
    amount = _amount(match)
    if amount is None:
        return None
    return ParsedTourPrice(
        amount=amount,
        currency=_currency(match.group("currency")),
        source_text=" ".join(match.group("source").split()),
        is_from=bool(match.groupdict().get("from")),
    )


__all__ = ["ParsedTourPrice", "parse_tour_price"]
