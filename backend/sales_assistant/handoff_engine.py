from __future__ import annotations

from dataclasses import dataclass

from backend.sales_assistant.handoff import (
    HandoffDecision,
    HandoffPriority,
    HandoffReason,
)


@dataclass(frozen=True, slots=True)
class _IntentRule:
    reason: HandoffReason
    markers: tuple[str, ...]
    priority: HandoffPriority = HandoffPriority.NORMAL


_RULES: tuple[_IntentRule, ...] = (
    _IntentRule(
        HandoffReason.EXPLICIT_HANDOFF_REQUEST,
        (
            "свяжите с менеджером",
            "свяжите меня с менеджером",
            "связаться с менеджером",
            "позовите менеджера",
            "передайте менеджеру",
            "хочу поговорить с человеком",
            "нужен человек",
            "перезвоните мне",
            "свяжитесь со мной",
        ),
        HandoffPriority.HIGH,
    ),
    _IntentRule(
        HandoffReason.BOOKING_REQUEST,
        (
            "хочу забронировать",
            "можно забронировать",
            "забронировать место",
            "запишите меня на тур",
            "хочу записаться на тур",
            "оставить заявку на тур",
            "оформить бронирование",
        ),
        HandoffPriority.HIGH,
    ),
    _IntentRule(
        HandoffReason.AVAILABILITY_REQUEST,
        (
            "есть ли места",
            "остались места",
            "свободные места",
            "актуальное наличие",
            "есть в наличии",
            "товар в наличии",
            "можно заказать",
        ),
    ),
    _IntentRule(
        HandoffReason.PERSONAL_CONDITIONS,
        (
            "индивидуальные условия",
            "индивидуальный маршрут",
            "индивидуальный тур",
            "особые условия",
            "поехать отдельно",
            "персональная консультация",
        ),
    ),
    _IntentRule(
        HandoffReason.PAYMENT_QUESTION,
        (
            "как оплатить",
            "способы оплаты",
            "оплата частями",
            "можно в рассрочку",
            "оплатить в рассрочку",
            "есть рассрочка",
            "предоплата",
            "условия оплаты",
        ),
    ),
)


class HandoffEngine:
    """Detect manager-only sales intents before the knowledge answer pipeline.

    The engine is deterministic and independent from response wording, storage,
    and UI. New intents are added as declarative rules instead of branching in
    the sales service.
    """

    def evaluate(self, message: str, *, topic: str | None = None) -> HandoffDecision:
        normalised = self._normalise(message)
        for rule in _RULES:
            if any(marker in normalised for marker in rule.markers):
                return HandoffDecision.transfer(
                    rule.reason,
                    priority=rule.priority,
                    user_message=message.strip(),
                )
        return HandoffDecision.continue_with_ai()

    @staticmethod
    def _normalise(value: str) -> str:
        return " ".join(value.casefold().replace("ё", "е").split())


__all__ = ["HandoffEngine"]
