from __future__ import annotations

import json
import re
from datetime import datetime

from backend.config import DIALOGS_FILE, EMAIL_TO
from backend.rag.product_search import (
    ProductMatch,
    format_price,
    search_products,
)
from backend.rag.dynamic_query_router import route_query
from backend.rag.retriever import (
    ENTITY_LABELS,
    SearchResult,
    detect_entity,
    search,
)


HUMAN_TRIGGERS = {
    "менеджер", "человек", "оператор", "администратор",
    "свяжитесь", "позвоните", "напишите мне", "живой",
}

CONTACT_TRIGGERS = {
    "@", "+7", "+371", "whatsapp", "telegram", "телеграм",
}


def wants_human(message: str) -> bool:
    lowered = message.lower()
    return any(trigger in lowered for trigger in HUMAN_TRIGGERS)


def looks_like_contact(message: str) -> bool:
    lowered = message.lower()
    has_phone = bool(
        re.search(r"(\+?\d[\d\s\-\(\)]{7,}\d)", message)
    )
    return has_phone or any(
        trigger in lowered for trigger in CONTACT_TRIGGERS
    )


def save_dialog(
    user_message: str,
    answer: str,
    status: str,
    sources: list[SearchResult] | None = None,
    product_sources: list[ProductMatch] | None = None,
) -> None:
    DIALOGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    source_items = []

    for source in sources or []:
        source_items.append(
            {
                "title": source.title,
                "url": source.url,
                "score": round(source.score, 2),
                "page_type": source.page_type,
            }
        )

    for match in product_sources or []:
        source_items.append(
            {
                "title": match.page.get("title"),
                "url": match.page.get("url"),
                "score": round(match.score, 2),
                "page_type": "product",
            }
        )

    record = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "user_message": user_message,
        "answer": answer,
        "status": status,
        "sources": source_items,
    }

    with DIALOGS_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def clean_inline(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_dates(text: str) -> str | None:
    pattern = (
        r"\b\d{1,2}\s*[–—-]\s*\d{1,2}\s+"
        r"(?:января|февраля|марта|апреля|мая|июня|июля|"
        r"августа|сентября|октября|ноября|декабря)"
        r"(?:\s+\d{4})?\b"
    )
    match = re.search(pattern, text.lower())
    return match.group(0) if match else None


def extract_duration(text: str) -> str | None:
    match = re.search(
        r"\b(\d{1,2})\s*(?:дней|дня|день)\b",
        text.lower(),
    )
    return f"{match.group(1)} дней" if match else None


def extract_country(text: str) -> str | None:
    countries = (
        "Индия", "Тибет", "Непал", "Бутан",
        "Россия", "Монголия", "Шри-Ланка",
    )
    lowered = text.lower()

    for country in countries:
        if country.lower() in lowered:
            return country

    return None


def first_meaningful_sentence(text: str, limit: int = 220) -> str | None:
    cleaned = clean_inline(text)

    for sentence in re.split(r"(?<=[.!?])\s+", cleaned):
        sentence = sentence.strip()
        if 45 <= len(sentence) <= limit:
            return sentence

    return None


def build_tour_answer(
    query: str,
    results: list[SearchResult],
) -> tuple[str, bool]:
    entity = detect_entity(query)
    tours = [item for item in results if item.page_type == "tour"]

    if not tours:
        label = ENTITY_LABELS.get(entity, "этому направлению")
        catalogs = [
            item for item in results
            if item.page_type == "tour_catalog"
        ]

        answer = (
            "На сайте пока не найдена отдельная карточка тура "
            f"по направлению «{label}»."
        )

        if catalogs:
            answer += (
                "\n\nАктуальные путешествия:\n"
                f"{catalogs[0].url}"
            )

        answer += (
            "\n\nЯ не буду предлагать другой тур вместо запрошенного. "
            "Могу передать интерес менеджеру."
        )
        return answer, True

    tour = tours[0]
    text = clean_inline(tour.content)
    details = []

    country = extract_country(text)
    dates = extract_dates(text)
    duration = extract_duration(text)

    if country:
        details.append(f"Направление: {country}")
    if dates:
        details.append(f"Даты: {dates}")
    if duration:
        details.append(f"Продолжительность: {duration}")

    lines = [f"Нашёл подходящий тур: {tour.title}."]

    if details:
        lines.append("\n".join(f"• {item}" for item in details))

    lines.append(f"Подробнее: {tour.url}")
    lines.append("Могу помочь оставить заявку на этот тур.")

    return "\n\n".join(lines), False


def build_product_answer(
    query: str,
) -> tuple[str, bool, list[ProductMatch]]:
    parsed, matches = search_products(query, limit=5)

    if not matches:
        # Не выполняем резервный поиск по страницам, турам или общим текстам.
        answer = (
            "В опубликованном каталоге я не нашёл товар с таким названием "
            "или параметрами.\n\n"
            "Проверьте написание названия. Если оно верное, товар может быть "
            "временно не опубликован или доступен только под заказ.\n\n"
            "Могу передать запрос менеджеру для уточнения."
        )
        return answer, True, []

    best = matches[0]
    page = best.page
    price = format_price(page)
    category = page.get("category")
    lines = [f"Нашёл подходящий товар: {page.get('title')}."]

    details = []

    if category:
        details.append(f"Категория: {category}")
    if best.size_cm is not None:
        details.append(f"Размер: около {best.size_cm:g} см")
    if price:
        details.append(f"Цена: {price}")

    if details:
        lines.append("\n".join(f"• {item}" for item in details))

    description = first_meaningful_sentence(
        str(page.get("text", ""))
    )

    if description:
        lines.append(description)

    lines.append(f"Страница товара: {page.get('url')}")
    lines.append(
        "Могу передать менеджеру вопрос о наличии или заказе."
    )

    return "\n\n".join(lines), False, matches


def build_psychologist_answer(
    results: list[SearchResult],
) -> tuple[str, bool]:
    if not results:
        return (
            "Я не нашёл точную информацию о консультации. "
            f"Передам вопрос менеджеру: {EMAIL_TO}",
            True,
        )

    page = results[0]
    text = page.content.lower()
    details = []

    if "евгения драй" in text:
        details.append(
            "Консультации проводит Евгения Драй — психолог и буддолог."
        )

    if "30 минут" in text and "бесплат" in text:
        details.append("Первая консультация 30 минут — бесплатно.")

    answer = "Да, консультации доступны."

    if details:
        answer += "\n\n" + "\n".join(f"• {item}" for item in details)

    answer += f"\n\nЗапись и подробности: {page.url}"
    return answer, False


def build_contacts_answer(results: list[SearchResult]) -> tuple[str, bool]:
    contacts = [
        item for item in results
        if item.page_type in {"contacts", "general"}
        and (
            "контакт" in item.title.lower()
            or "join-us" in item.url.lower()
        )
    ]

    if not contacts:
        return (
            f"Напишите менеджеру студии: {EMAIL_TO}",
            False,
        )

    page = contacts[0]
    return (
        "Контактная информация студии:\n\n"
        f"{page.url}\n\n"
        f"Email: {EMAIL_TO}",
        False,
    )


def build_reviews_answer(results: list[SearchResult]) -> tuple[str, bool]:
    reviews = [item for item in results if item.page_type == "reviews"]

    if not reviews:
        return (
            "Страница отзывов сейчас не найдена. "
            f"Можно уточнить у менеджера: {EMAIL_TO}",
            True,
        )

    return (
        "Отзывы о студии и поездках:\n\n"
        f"{reviews[0].url}",
        False,
    )


def build_general_answer(
    results: list[SearchResult],
) -> tuple[str, bool]:
    if not results:
        return (
            "Я не нашёл точной информации об этом на сайте. "
            "Могу передать вопрос менеджеру.",
            True,
        )

    source = results[0]
    description = first_meaningful_sentence(source.content)

    if not description:
        description = clean_inline(source.content)[:250] + "…"

    return (
        "По информации с сайта «Свет Лотоса»:\n\n"
        f"{description}\n\n"
        f"Источник: {source.url}",
        False,
    )


def chat(message: str) -> dict:
    message = message.strip()

    if not message:
        return {
            "answer": "Напишите вопрос.",
            "status": "empty",
            "sources": [],
            "handoff": False,
        }

    if wants_human(message):
        answer = (
            "Хорошо, я передам ваш запрос менеджеру. "
            f"Контакт для заявок: {EMAIL_TO}"
        )
        save_dialog(message, answer, "handoff_requested")
        return {
            "answer": answer,
            "status": "handoff_requested",
            "sources": [],
            "handoff": True,
        }

    if looks_like_contact(message):
        answer = (
            "Спасибо, контактные данные зафиксированы. "
            f"Обращение будет передано менеджеру на {EMAIL_TO}."
        )
        save_dialog(message, answer, "lead_collected")
        return {
            "answer": answer,
            "status": "lead_collected",
            "sources": [],
            "handoff": True,
        }

    route = route_query(message)

    if route.intent == "product":
        answer, handoff, product_matches = build_product_answer(message)
        status = "product_answer" if not handoff else "product_not_found"
        save_dialog(
            message,
            answer,
            status,
            product_sources=product_matches,
        )
        return {
            "answer": answer,
            "status": status,
            "sources": [
                {
                    "title": match.page.get("title"),
                    "url": match.page.get("url"),
                    "score": round(match.score, 2),
                    "page_type": "product",
                }
                for match in product_matches
            ],
            "handoff": handoff,
        }

    if route.intent == "unknown":
        answer = (
            "Я не смог надёжно определить, о чём ваш вопрос. "
            "Уточните, пожалуйста: это товар, тур или консультация?\n\n"
            "Чтобы не вводить вас в заблуждение, я не буду подставлять "
            "случайную страницу сайта."
        )
        save_dialog(message, answer, "clarification_required")
        return {
            "answer": answer,
            "status": "clarification_required",
            "sources": [],
            "handoff": False,
        }

    results = search(message, limit=5)

    if route.intent == "tour":
        answer, handoff = build_tour_answer(message, results)
        status = "tour_answer" if not handoff else "tour_exact_not_found"
    elif route.intent == "psychologist":
        answer, handoff = build_psychologist_answer(results)
        status = (
            "psychologist_answer"
            if not handoff
            else "psychologist_not_found"
        )
    elif route.intent == "contacts":
        answer, handoff = build_contacts_answer(results)
        status = "contacts_answer"
    elif route.intent == "reviews":
        answer, handoff = build_reviews_answer(results)
        status = "reviews_answer" if not handoff else "reviews_not_found"
    else:
        answer, handoff = build_general_answer(results)
        status = "general_answer" if not handoff else "no_context_handoff"

    save_dialog(message, answer, status, sources=results)

    return {
        "answer": answer,
        "status": status,
        "sources": [
            {
                "title": source.title,
                "url": source.url,
                "score": round(source.score, 2),
                "page_type": source.page_type,
            }
            for source in results
        ],
        "handoff": handoff,
    }
