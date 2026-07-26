from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from backend.catalog.product_intelligence import normalize


class ConversationDecisionType(StrEnum):
    SHOW_RESULTS = "show_results"
    ASK_CLARIFICATION = "ask_clarification"


@dataclass(frozen=True, slots=True)
class ConversationDecision:
    action: ConversationDecisionType
    clarification_type: str | None = None
    question: str | None = None


_GIFT_MARKERS = ("подар", "в подарок")
_HOME_MARKERS = ("что-нибудь домой", "что нибудь домой", "что-то домой", "что то домой", "для дома")
_SPECIFIC_PRODUCT_MARKERS = (
    "стату", "тханк", "танк", "наклей", "подвес", "кулон", "амулет",
    "ваджр", "колоколь", "чётк", "четк", "благовон", "аспект",
    "калачакр", "тар", "будд", "милареп",
)


def decide_conversation_action(query: str, *, clarification_already_asked: bool = False) -> ConversationDecision:
    """Choose between immediate commercial results and one useful question.

    The decision is intentionally deterministic and narrow.  It does not ask a
    question when the user has already named a product type/aspect/direction,
    and it never asks a second clarification for the same selection turn.
    """

    if clarification_already_asked:
        return ConversationDecision(ConversationDecisionType.SHOW_RESULTS)

    text = normalize(query)
    has_specific_marker = any(marker in text for marker in _SPECIFIC_PRODUCT_MARKERS)

    if any(marker in text for marker in _GIFT_MARKERS) and not has_specific_marker:
        return ConversationDecision(
            ConversationDecisionType.ASK_CLARIFICATION,
            clarification_type="gift_purpose",
            question="Это подарок для буддийской практики или скорее красивый сувенир?",
        )

    if any(marker in text for marker in _HOME_MARKERS) and not has_specific_marker:
        return ConversationDecision(
            ConversationDecisionType.ASK_CLARIFICATION,
            clarification_type="home_purpose",
            question="Вы ищете предмет для домашнего алтаря или декоративную вещь для интерьера?",
        )

    return ConversationDecision(ConversationDecisionType.SHOW_RESULTS)


__all__ = [
    "ConversationDecision",
    "ConversationDecisionType",
    "decide_conversation_action",
]
