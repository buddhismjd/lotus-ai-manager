from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NobleTonePolicy:
    """Central wording policy for warm, respectful commercial dialogue."""

    greeting: str = (
        "Добрый день! Буду рада помочь! Подобрать путешествие или товар? "
        "Записать на бесплатную консультацию психолога-буддолога?"
    )
    empty_request: str = (
        "Буду рада помочь. Напишите, пожалуйста, что Вас сейчас интересует."
    )
    email_offer: str = (
        "Могу бережно сохранить эту информацию для Вас и отправить её на email, "
        "чтобы Вы могли вернуться к ней в удобное время."
    )
    email_request: str = (
        "Напишите, пожалуйста, Ваш email. Перед сохранением я обязательно "
        "укажу, какую именно информацию Вы будете получать."
    )
    email_invalid: str = (
        "Похоже, в адресе есть неточность. Пожалуйста, проверьте email и отправьте его ещё раз."
    )
    email_saved: str = (
        "Благодарю Вас. Email и выбранная тематика сохранены."
    )


TONE = NobleTonePolicy()


def warm_missing_price(subject: str) -> str:
    return (
        f"Стоимость «{subject}» пока не указана на сайте и ещё не опубликована. "
        "Я ничего не буду придумывать и не стану вводить Вас в заблуждение. Могу сохранить Ваш интерес, "
        "чтобы менеджер сообщил актуальную стоимость и наличие мест."
    )


def warm_missing_date(subject: str) -> str:
    return (
        f"Точная дата «{subject}» пока не опубликована. "
        "Могу сохранить Ваш интерес и передать вопрос менеджеру."
    )


__all__ = [
    "NobleTonePolicy",
    "TONE",
    "email_request_for_topic",
    "email_saved_for_topic",
    "warm_missing_date",
    "warm_missing_price",
]


def email_request_for_topic(topic: str) -> str:
    if topic == "tour":
        return (
            "Напишите, пожалуйста, Ваш email. Я сохраню его только для отправки информации "
            "о новых турах и путешествиях студии «Свет Лотоса»."
        )
    if topic == "product":
        return (
            "Напишите, пожалуйста, Ваш email. Я сохраню его только для отправки информации "
            "о новых товарах магазина «Свет Лотоса»."
        )
    if topic == "psychologist":
        return (
            "Напишите, пожалуйста, Ваш email. Я сохраню его только для отправки информации "
            "о консультации психолога-буддолога и способах записи."
        )
    return TONE.email_request


def email_saved_for_topic(topic: str) -> str:
    if topic == "tour":
        return "Благодарю Вас. Теперь мы сможем сообщать Вам о новых путешествиях."
    if topic == "product":
        return "Благодарю Вас. Теперь мы сможем сообщать Вам о новых товарах."
    if topic == "psychologist":
        return (
            "Благодарю Вас. Email сохранён для отправки информации "
            "о консультации и способах записи."
        )
    return TONE.email_saved
