from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class NextActionType(StrEnum):
    NONE = "none"
    SHOW_TOUR_DETAILS = "show_tour_details"
    SHOW_PROGRAM = "show_program"
    SHOW_PRICE = "show_price"
    SHOW_RELATED_TOURS = "show_related_tours"
    SHOW_RELATED_PRODUCTS = "show_related_products"
    BOOK_CONSULTATION = "book_consultation"
    LEAVE_CONTACT = "leave_contact"
    TRANSFER_MANAGER = "transfer_manager"
    ASK_PREFERENCE = "ask_preference"
    ASK_NAME = "ask_name"
    ASK_CONTACT_METHOD = "ask_contact_method"
    ASK_CONTACT_VALUE = "ask_contact_value"
    LEAD_SAVED = "lead_saved"
    EMAIL_FOLLOWUP = "email_followup"
    EMAIL_SAVED = "email_saved"
    OPEN_URL = "open_url"
    ARTISAN_SELECTION = "artisan_selection"


@dataclass(frozen=True, slots=True)
class DialogueSuggestion:
    action: NextActionType
    label: str
    message: str = ""
    url: str | None = None


@dataclass(frozen=True, slots=True)
class DialoguePlan:
    next_action: NextActionType = NextActionType.NONE
    suggestions: tuple[DialogueSuggestion, ...] = ()
    requires_manager: bool = False


class SalesDialogueManager:
    """Choose the next useful sales action without changing knowledge lookup."""

    def plan(
        self,
        *,
        strategy: str,
        topic: str,
        kind: str,
        title: str | None = None,
        needs_manager: bool = False,
    ) -> DialoguePlan:
        subject = title or "этот вариант"

        if strategy == "tour_list":
            return DialoguePlan(
                next_action=NextActionType.ASK_PREFERENCE,
                suggestions=(
                    DialogueSuggestion(
                        NextActionType.SHOW_TOUR_DETAILS,
                        "Рассказать о Кайласе",
                        "Расскажите подробнее про тур на Кайлас",
                    ),
                    DialogueSuggestion(
                        NextActionType.TRANSFER_MANAGER,
                        "Помочь с выбором",
                        "Помогите подобрать подходящий тур",
                    ),
                    DialogueSuggestion(
                        NextActionType.EMAIL_FOLLOWUP,
                        "Получать новые туры на email",
                        "Хочу получать информацию о новых турах на email",
                    ),
                ),
                requires_manager=needs_manager,
            )

        if strategy == "tour_price":
            return DialoguePlan(
                next_action=(
                    NextActionType.LEAVE_CONTACT
                    if needs_manager
                    else NextActionType.SHOW_PROGRAM
                ),
                suggestions=(
                    DialogueSuggestion(
                        NextActionType.LEAVE_CONTACT,
                        "Оставить заявку",
                        f"Хочу оставить заявку на {subject}",
                    ),
                    DialogueSuggestion(
                        NextActionType.SHOW_PROGRAM,
                        "Программа тура",
                        f"Расскажите программу тура {subject}",
                    ),
                    DialogueSuggestion(
                        NextActionType.TRANSFER_MANAGER,
                        "Связаться с менеджером",
                        f"Хочу связаться с менеджером по туру {subject}",
                    ),
                    DialogueSuggestion(
                        NextActionType.EMAIL_FOLLOWUP,
                        "Получать новые туры на email",
                        "Хочу получать информацию о новых турах на email",
                    ),
                ),
                requires_manager=needs_manager,
            )

        if topic == "tour":
            return DialoguePlan(
                next_action=NextActionType.SHOW_PROGRAM,
                suggestions=(
                    DialogueSuggestion(
                        NextActionType.SHOW_PROGRAM,
                        "Программа",
                        f"Что входит в программу тура {subject}?",
                    ),
                    DialogueSuggestion(
                        NextActionType.SHOW_PRICE,
                        "Стоимость",
                        f"Сколько стоит тур {subject}?",
                    ),
                    DialogueSuggestion(
                        NextActionType.LEAVE_CONTACT,
                        "Оставить заявку",
                        f"Хочу оставить заявку на {subject}",
                    ),
                    DialogueSuggestion(
                        NextActionType.EMAIL_FOLLOWUP,
                        "Получать новые туры на email",
                        "Хочу получать информацию о новых турах на email",
                    ),
                ),
                requires_manager=needs_manager,
            )

        if topic == "product":
            return DialoguePlan(
                next_action=NextActionType.SHOW_RELATED_PRODUCTS,
                suggestions=(
                    DialogueSuggestion(
                        NextActionType.SHOW_RELATED_PRODUCTS,
                        "Похожие товары",
                        f"Покажите похожие товары на {subject}",
                    ),
                    DialogueSuggestion(
                        NextActionType.TRANSFER_MANAGER,
                        "Помочь с выбором",
                        f"Нужна помощь с выбором товара {subject}",
                    ),
                    DialogueSuggestion(
                        NextActionType.EMAIL_FOLLOWUP,
                        "Получать новые товары на email",
                        "Хочу получать информацию о новых товарах на email",
                    ),
                ),
                requires_manager=needs_manager,
            )

        if topic == "psychologist":
            return DialoguePlan(
                next_action=NextActionType.BOOK_CONSULTATION,
                suggestions=(
                    DialogueSuggestion(
                        NextActionType.BOOK_CONSULTATION,
                        "Записаться",
                        "Хочу записаться на консультацию буддолога-психолога",
                    ),
                    DialogueSuggestion(
                        NextActionType.SHOW_PRICE,
                        "Стоимость",
                        "Сколько стоит консультация буддолога-психолога?",
                    ),
                    DialogueSuggestion(
                        NextActionType.TRANSFER_MANAGER,
                        "Задать вопрос",
                        "Хочу задать вопрос специалисту",
                    ),
                    DialogueSuggestion(
                        NextActionType.EMAIL_FOLLOWUP,
                        "Получить информацию на email",
                        "Отправьте, пожалуйста, информацию о консультации на email",
                    ),
                ),
                requires_manager=needs_manager,
            )

        if topic == "contacts" or kind == "fallback":
            return DialoguePlan(
                next_action=NextActionType.TRANSFER_MANAGER,
                suggestions=(
                    DialogueSuggestion(
                        NextActionType.LEAVE_CONTACT,
                        "Оставить контакт",
                        "Хочу оставить контакт для связи",
                    ),
                ),
                requires_manager=True,
            )

        return DialoguePlan(requires_manager=needs_manager)


__all__ = [
    "DialoguePlan",
    "DialogueSuggestion",
    "NextActionType",
    "SalesDialogueManager",
]
