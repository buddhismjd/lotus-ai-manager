from __future__ import annotations

from dataclasses import dataclass

from backend.sales_assistant.handoff import HandoffReason


_REASON_LABELS: dict[HandoffReason, str] = {
    HandoffReason.KNOWLEDGE_NOT_FOUND: "вопрос отсутствует в базе знаний",
    HandoffReason.MANAGER_REQUIRED: "требуется консультация менеджера",
    HandoffReason.BOOKING_REQUEST: "запрос на бронирование",
    HandoffReason.AVAILABILITY_REQUEST: "уточнение наличия мест или товара",
    HandoffReason.PERSONAL_CONDITIONS: "индивидуальные условия",
    HandoffReason.PAYMENT_QUESTION: "вопрос по оплате или рассрочке",
    HandoffReason.EXPLICIT_HANDOFF_REQUEST: "клиент попросил связать с менеджером",
}


@dataclass(frozen=True, slots=True)
class LeadSummaryContext:
    interest_title: str | None
    last_question: str | None
    handoff_reason: HandoffReason
    topic: str | None = None


class LeadSummaryBuilder:
    """Build a deterministic manager summary without an LLM dependency."""

    def build(self, context: LeadSummaryContext) -> str:
        parts: list[str] = []
        interest = self._clean(context.interest_title)
        question = self._clean(context.last_question)

        if interest:
            parts.append(f"Клиент интересуется: {interest}.")
        elif context.topic:
            parts.append(f"Тема обращения: {self._clean(context.topic)}.")

        if question:
            parts.append(f"Последний вопрос: {question}.")

        parts.append(f"Причина передачи: {_REASON_LABELS[context.handoff_reason]}.")
        return " ".join(parts)

    @staticmethod
    def _clean(value: str | None) -> str:
        text = " ".join((value or "").strip().split())
        return text.rstrip(".!?")


__all__ = ["LeadSummaryBuilder", "LeadSummaryContext"]
