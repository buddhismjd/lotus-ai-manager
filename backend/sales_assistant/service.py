from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from backend.rag.dynamic_query_router import route_query
from backend.catalog.collection_builder import build_product_collection
from backend.tours.collection_builder import build_tour_collection, detect_country
from backend.sales_assistant.dialogue import (
    DialogueSuggestion,
    NextActionType,
    SalesDialogueManager,
)
from backend.sales_assistant.formatter import format_sales_response, format_tour_list
from backend.sales_assistant.leads import LeadRepository
from backend.sales_assistant.state import DialogueStage, DialogueState, DialogueStateStore
from backend.sales_assistant.strategy import choose_strategy
from backend.services.bodhi_service import answer_query
from backend.services.response_builder import BuiltResponse
from backend.structured_catalog.models import StructuredTour
from backend.structured_catalog.repositories import StructuredTourRepository

SalesTopic = Literal["tour", "product", "psychologist", "contacts", "unknown"]


@dataclass(frozen=True, slots=True)
class SalesReply:
    answer: str
    kind: str
    topic: SalesTopic
    title: str | None = None
    url: str | None = None
    needs_manager: bool = False
    next_action: NextActionType = NextActionType.NONE
    suggestions: tuple[DialogueSuggestion, ...] = ()
    dialogue_stage: str = DialogueStage.DISCOVERY.value
    lead_id: int | None = None
    items: tuple[dict, ...] = ()


class SalesAssistant:
    """Stateful sales layer over the established Bodhi service."""

    def __init__(self) -> None:
        self._states = DialogueStateStore()
        self._dialogue = SalesDialogueManager()
        self._tours = StructuredTourRepository()
        self._leads = LeadRepository()

    def reset(self, session_id: str) -> None:
        self._states.reset(session_id)

    def reply(self, message: str, session_id: str = "default") -> SalesReply:
        query = message.strip()
        if not query:
            return SalesReply("Напишите вопрос.", "empty", "unknown")

        state = self._states.get(session_id)

        if state.stage != DialogueStage.DISCOVERY:
            return self._handle_lead_capture(query, state)

        if self._starts_lead_capture(query):
            state.start_lead_capture()
            return SalesReply(
                answer=(
                    "Отлично, я помогу передать заявку менеджеру. "
                    "Как я могу к Вам обращаться?"
                ),
                kind="lead_capture",
                topic=self._state_topic(state),
                next_action=NextActionType.ASK_NAME,
                dialogue_stage=state.stage.value,
            )

        route = route_query(query)
        topic = self._topic(route.intent)
        if topic == "unknown" and self._is_follow_up(query):
            topic = self._state_topic(state)

        decision = choose_strategy(query, topic)

        if topic == "product":
            product_items = build_product_collection(query)
            if product_items:
                state.last_query = query
                state.topic = "product"
                answer = (
                    f"Нашла {len(product_items)} подходящих "
                    + ("товар." if len(product_items) == 1 else "товара." if len(product_items) < 5 else "товаров.")
                    + " Все варианты представлены ниже."
                )
                return self._with_dialogue(
                    SalesReply(
                        answer=answer,
                        kind="product_collection",
                        topic="product",
                        items=tuple(item.to_dict() for item in product_items),
                    ),
                    decision.strategy,
                )

        if topic == "tour" and detect_country(query):
            tour_items = build_tour_collection(query)
            country = detect_country(query)
            state.last_query = query
            state.topic = "tour"
            if tour_items:
                planned_only = all(item.status == "planned" for item in tour_items)
                answer = (
                    f"По направлению «{country}» опубликованных программ пока нет, "
                    "но готовится следующее путешествие:"
                    if planned_only else
                    f"Нашла путешествия по направлению «{country}»:"
                )
                return self._with_dialogue(
                    SalesReply(
                        answer=answer,
                        kind="tour_collection",
                        topic="tour",
                        items=tuple(item.to_dict() for item in tour_items),
                        needs_manager=planned_only,
                    ),
                    decision.strategy,
                )
            return self._with_dialogue(
                SalesReply(
                    answer=f"Сейчас я не нашла опубликованных или планируемых путешествий по направлению «{country}».",
                    kind="tour_collection",
                    topic="tour",
                ),
                decision.strategy,
            )

        if self._asks_for_tour_selection(query) and state.candidate_tour_ids:
            state.last_query = query
            state.topic = "tour"
            state.goal = "choose_tour"
            return self._tour_selection_reply(state)

        if decision.strategy == "tour_list":
            tours = (
                self._tours.list_by_month(decision.month)
                if decision.month is not None
                else self._tours.list_all()
            )
            state.last_query = query
            state.remember_tour_list(tours, month=decision.month)
            needs_manager = not tours
            plan = self._dialogue.plan(
                strategy=decision.strategy,
                topic="tour",
                kind="tour_list",
                needs_manager=needs_manager,
            )
            return SalesReply(
                answer=format_tour_list(tours, month=decision.month),
                kind="tour_list",
                topic="tour",
                needs_manager=plan.requires_manager,
                next_action=plan.next_action,
                suggestions=plan.suggestions,
            )

        if topic == "psychologist":
            state.topic = "psychologist"
            state.goal = "book_consultation"
            state.last_query = query
            return self._with_dialogue(
                self._psychologist_reply(query),
                decision.strategy,
            )

        if topic == "contacts":
            state.topic = "contacts"
            state.goal = "contact_manager"
            state.last_query = query
            return self._with_dialogue(self._contacts_reply(), decision.strategy)

        matched_title = getattr(route, "matched_title", None)
        matched_url = getattr(route, "matched_url", None)
        matched_tour = self._find_structured_tour(matched_title, matched_url)
        if matched_tour is None and topic == "tour":
            matched_tour = self._resolve_tour_from_state(query, state)

        if matched_tour is not None:
            state.remember_active_tour(matched_tour)

        if decision.strategy == "tour_price" and matched_tour is not None:
            state.last_query = query
            return self._with_dialogue(
                self._tour_price_reply(matched_tour),
                decision.strategy,
            )

        if decision.strategy == "tour_date" and matched_tour is not None:
            state.last_query = query
            return self._with_dialogue(
                self._tour_date_reply(matched_tour),
                decision.strategy,
            )

        if topic == "tour" and matched_tour is None and state.candidate_tour_ids:
            if self._is_ambiguous_tour_follow_up(query):
                state.last_query = query
                return self._ask_which_tour(state)

        previous = state.last_query
        effective_query = query
        if topic in {"tour", "product"} and route.intent == "unknown" and previous:
            effective_query = f"{previous}. {query}"

        raw_response = answer_query(effective_query)
        if raw_response.kind == "fallback" and matched_tour is not None:
            raw_response = BuiltResponse(
                kind="tour",
                text=matched_tour.description,
                title=matched_tour.title,
                url=matched_tour.url,
            )
        response = format_sales_response(raw_response)
        resolved_topic = topic if topic != "unknown" else self._topic(response.kind)

        if response.kind == "tour":
            resolved = self._find_structured_tour(response.title, response.url)
            if resolved is not None:
                state.remember_active_tour(resolved)

        state.last_query = query
        if resolved_topic != "unknown":
            state.topic = resolved_topic

        if decision.strategy == "tour_price" and response.kind == "tour":
            tour = self._find_structured_tour(response.title, response.url)
            if tour is None or tour.price is None:
                title = response.title or (tour.title if tour else "этот тур")
                reply = SalesReply(
                    answer=(
                        f"Стоимость тура «{title}» пока не опубликована на сайте. "
                        "Я не буду придумывать цену. Могу помочь оставить заявку, "
                        "и менеджер сообщит актуальную стоимость и наличие мест."
                    ),
                    kind="tour_price",
                    topic="tour",
                    title=response.title,
                    url=response.url,
                    needs_manager=True,
                )
                return self._with_dialogue(reply, decision.strategy)

        needs_manager = response.kind == "fallback"
        reply = SalesReply(
            answer=response.text,
            kind=response.kind,
            topic=resolved_topic,
            title=response.title,
            url=response.url,
            needs_manager=needs_manager,
        )
        return self._with_dialogue(reply, decision.strategy)

    def _handle_lead_capture(self, query: str, state: DialogueState) -> SalesReply:
        if self._cancels_lead_capture(query):
            state.stage = DialogueStage.DISCOVERY
            state.goal = None
            state.lead.clear()
            return SalesReply(
                "Хорошо, оформление заявки отменено. Можем продолжить подбор.",
                "lead_cancelled",
                self._state_topic(state),
                dialogue_stage=state.stage.value,
            )

        if state.stage == DialogueStage.LEAD_NAME:
            name = query.strip()
            if len(name) < 2 or len(name) > 80:
                return SalesReply(
                    "Напишите, пожалуйста, Ваше имя.",
                    "lead_capture",
                    self._state_topic(state),
                    next_action=NextActionType.ASK_NAME,
                    dialogue_stage=state.stage.value,
                )
            state.lead.name = name
            state.stage = DialogueStage.LEAD_CONTACT_METHOD
            return SalesReply(
                "Спасибо. Какой способ связи Вам удобнее: Telegram, WhatsApp, телефон или email?",
                "lead_capture",
                self._state_topic(state),
                next_action=NextActionType.ASK_CONTACT_METHOD,
                suggestions=(
                    DialogueSuggestion(NextActionType.ASK_CONTACT_METHOD, "Telegram", "Telegram"),
                    DialogueSuggestion(NextActionType.ASK_CONTACT_METHOD, "WhatsApp", "WhatsApp"),
                    DialogueSuggestion(NextActionType.ASK_CONTACT_METHOD, "Телефон", "Телефон"),
                    DialogueSuggestion(NextActionType.ASK_CONTACT_METHOD, "Email", "Email"),
                ),
                dialogue_stage=state.stage.value,
            )

        if state.stage == DialogueStage.LEAD_CONTACT_METHOD:
            method = self._parse_contact_method(query)
            if method is None:
                return SalesReply(
                    "Выберите, пожалуйста: Telegram, WhatsApp, телефон или email.",
                    "lead_capture",
                    self._state_topic(state),
                    next_action=NextActionType.ASK_CONTACT_METHOD,
                    dialogue_stage=state.stage.value,
                )
            state.lead.contact_method = method
            state.stage = DialogueStage.LEAD_CONTACT_VALUE
            labels = {
                "telegram": "Ваш Telegram, например @username",
                "whatsapp": "номер WhatsApp с кодом страны",
                "phone": "номер телефона с кодом страны",
                "email": "адрес электронной почты",
            }
            return SalesReply(
                f"Напишите, пожалуйста, {labels[method]}.",
                "lead_capture",
                self._state_topic(state),
                next_action=NextActionType.ASK_CONTACT_VALUE,
                dialogue_stage=state.stage.value,
            )

        if state.stage == DialogueStage.LEAD_CONTACT_VALUE:
            method = state.lead.contact_method or "phone"
            value = query.strip()
            if not self._valid_contact(method, value):
                return SalesReply(
                    "Контакт выглядит неполным. Проверьте его и отправьте ещё раз.",
                    "lead_capture",
                    self._state_topic(state),
                    next_action=NextActionType.ASK_CONTACT_VALUE,
                    dialogue_stage=state.stage.value,
                )
            state.lead.contact_value = value
            saved = self._leads.save(
                name=state.lead.name or "Посетитель сайта",
                contact_method=method,
                contact_value=value,
                interest=state.lead.interest,
                comment=f"Источник: AI Bodhi; тема: {state.topic}",
            )
            interest = state.lead.interest
            state.stage = DialogueStage.LEAD_COMPLETE
            answer = "Спасибо! Заявка сохранена и будет передана менеджеру."
            if interest and interest not in {"unknown", "contacts"}:
                answer += f" Интерес: «{interest}»."
            state.stage = DialogueStage.DISCOVERY
            state.goal = None
            state.lead.clear()
            return SalesReply(
                answer,
                "lead_saved",
                self._state_topic(state),
                needs_manager=True,
                next_action=NextActionType.LEAD_SAVED,
                dialogue_stage=DialogueStage.LEAD_COMPLETE.value,
                lead_id=saved.id,
            )

        state.stage = DialogueStage.DISCOVERY
        return SalesReply(
            "Давайте продолжим. Чем я могу помочь?",
            "lead_reset",
            self._state_topic(state),
            dialogue_stage=state.stage.value,
        )

    def _tour_selection_reply(self, state: DialogueState) -> SalesReply:
        tours = self._candidate_tours(state)
        if not tours:
            return self._with_dialogue(
                SalesReply(
                    answer=(
                        "Я не сохранил варианты для сравнения. "
                        "Напишите месяц или направление, и я покажу подходящие туры."
                    ),
                    kind="fallback",
                    topic="tour",
                    needs_manager=False,
                ),
                "tour_list",
            )

        cards: list[str] = ["Давайте подберём подходящий вариант из найденных туров:"]
        for tour in tours[:4]:
            facts = [f"🗻 {tour.title}"]
            if tour.schedule and tour.schedule.source_text:
                facts.append(f"📅 {tour.schedule.source_text}")
            if tour.duration_days:
                facts.append(f"⏱ {tour.duration_days} дней")
            if tour.countries:
                facts.append(f"📍 {', '.join(tour.countries)}")
            cards.append("\n".join(facts))

        cards.append(
            "Что для Вас важнее: духовное паломничество, треккинг, "
            "более спокойный маршрут или конкретная страна?"
        )
        suggestions = tuple(
            DialogueSuggestion(
                NextActionType.SHOW_TOUR_DETAILS,
                tour.title,
                f"Расскажите подробнее про {tour.title}",
            )
            for tour in tours[:3]
        )
        return SalesReply(
            answer="\n\n".join(cards),
            kind="tour_selection",
            topic="tour",
            next_action=NextActionType.ASK_PREFERENCE,
            suggestions=suggestions,
        )

    def _ask_which_tour(self, state: DialogueState) -> SalesReply:
        tours = self._candidate_tours(state)
        names = "\n".join(f"• {tour.title}" for tour in tours[:5])
        return SalesReply(
            answer=(
                "Уточните, пожалуйста, о каком из найденных туров идёт речь:\n"
                f"{names}"
            ),
            kind="tour_clarification",
            topic="tour",
            next_action=NextActionType.ASK_PREFERENCE,
            suggestions=tuple(
                DialogueSuggestion(
                    NextActionType.SHOW_TOUR_DETAILS,
                    tour.title,
                    f"Расскажите про {tour.title}",
                )
                for tour in tours[:3]
            ),
        )

    @staticmethod
    def _tour_price_reply(tour: StructuredTour) -> SalesReply:
        if tour.price is None:
            return SalesReply(
                answer=(
                    f"Стоимость тура «{tour.title}» пока не опубликована на сайте. "
                    "Я не буду придумывать цену. Могу помочь оставить заявку, "
                    "и менеджер сообщит актуальную стоимость и наличие мест."
                ),
                kind="tour_price",
                topic="tour",
                title=tour.title,
                url=tour.url,
                needs_manager=True,
            )
        return SalesReply(
            answer=f"Стоимость тура «{tour.title}»: {tour.price} {tour.currency}.",
            kind="tour_price",
            topic="tour",
            title=tour.title,
            url=tour.url,
        )

    @staticmethod
    def _tour_date_reply(tour: StructuredTour) -> SalesReply:
        if tour.schedule and tour.schedule.source_text:
            answer = f"Тур «{tour.title}» запланирован на {tour.schedule.source_text}."
            needs_manager = False
        else:
            answer = (
                f"Точная дата тура «{tour.title}» пока не опубликована. "
                "Могу передать вопрос менеджеру."
            )
            needs_manager = True
        return SalesReply(
            answer=answer,
            kind="tour_date",
            topic="tour",
            title=tour.title,
            url=tour.url,
            needs_manager=needs_manager,
        )

    def _with_dialogue(self, reply: SalesReply, strategy: str) -> SalesReply:
        plan = self._dialogue.plan(
            strategy=strategy,
            topic=reply.topic,
            kind=reply.kind,
            title=reply.title,
            needs_manager=reply.needs_manager,
        )
        return SalesReply(
            answer=reply.answer,
            kind=reply.kind,
            topic=reply.topic,
            title=reply.title,
            url=reply.url,
            needs_manager=plan.requires_manager,
            next_action=plan.next_action,
            suggestions=plan.suggestions,
            items=reply.items,
        )

    def _candidate_tours(self, state: DialogueState) -> list[StructuredTour]:
        tours: list[StructuredTour] = []
        for tour_id in state.candidate_tour_ids:
            tour = self._tours.get_by_id(tour_id)
            if tour is not None:
                tours.append(tour)
        return tours

    def _resolve_tour_from_state(
        self,
        query: str,
        state: DialogueState,
    ) -> StructuredTour | None:
        if state.active_url or state.active_title:
            active = self._find_structured_tour(state.active_title, state.active_url)
            if active is not None and self._is_follow_up(query):
                return active

        lowered = self._normalise(query)
        for tour in self._candidate_tours(state):
            title = self._normalise(tour.title)
            significant = [word for word in title.split() if len(word) >= 5]
            if any(word in lowered for word in significant):
                return tour
        return None

    def _find_structured_tour(
        self,
        title: str | None,
        url: str | None,
    ) -> StructuredTour | None:
        for tour in self._tours.list_all():
            if url and tour.url == url:
                return tour
            if title and tour.title == title:
                return tour
        return None

    @staticmethod
    def _state_topic(state: DialogueState) -> SalesTopic:
        if state.topic in {"tour", "product", "psychologist", "contacts"}:
            return state.topic  # type: ignore[return-value]
        return "unknown"

    @staticmethod
    def _topic(value: str) -> SalesTopic:
        if value in {"tour", "product", "psychologist", "contacts"}:
            return value  # type: ignore[return-value]
        return "unknown"

    @staticmethod
    def _normalise(value: str) -> str:
        return " ".join(value.casefold().replace("ё", "е").split())

    @classmethod
    def _asks_for_tour_selection(cls, query: str) -> bool:
        lowered = cls._normalise(query)
        return any(
            marker in lowered
            for marker in (
                "помогите подобрать",
                "помоги подобрать",
                "какой тур выбрать",
                "что посоветуете",
                "посоветуйте тур",
                "подходящий тур",
            )
        )

    @classmethod
    def _is_ambiguous_tour_follow_up(cls, query: str) -> bool:
        lowered = cls._normalise(query)
        return any(
            marker in lowered
            for marker in (
                "сколько стоит",
                "какая цена",
                "когда",
                "что входит",
                "расскажите подробнее",
                "подробнее",
            )
        )

    @staticmethod
    def _is_follow_up(query: str) -> bool:
        lowered = query.casefold()
        markers = (
            "сколько",
            "цена",
            "стоимость",
            "как записаться",
            "подробнее",
            "когда",
            "что входит",
            "помогите подобрать",
            "помоги подобрать",
        )
        return any(marker in lowered for marker in markers) or len(lowered.split()) <= 4

    @classmethod
    def _starts_lead_capture(cls, query: str) -> bool:
        lowered = cls._normalise(query)
        markers = (
            "оставить заявку",
            "оставить контакт",
            "контакт для связи",
            "хочу записаться",
            "свяжитесь со мной",
            "передайте менеджеру",
        )
        return any(marker in lowered for marker in markers)

    @classmethod
    def _cancels_lead_capture(cls, query: str) -> bool:
        lowered = cls._normalise(query)
        return any(marker in lowered for marker in ("отмена", "не хочу", "назад", "прекратить"))

    @classmethod
    def _parse_contact_method(cls, query: str) -> str | None:
        lowered = cls._normalise(query)
        if "telegram" in lowered or "телеграм" in lowered:
            return "telegram"
        if "whatsapp" in lowered or "ватсап" in lowered or "вотсап" in lowered:
            return "whatsapp"
        if "email" in lowered or "почт" in lowered or "e-mail" in lowered:
            return "email"
        if "телефон" in lowered or "номер" in lowered:
            return "phone"
        return None

    @staticmethod
    def _valid_contact(method: str, value: str) -> bool:
        compact = value.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if method == "email":
            return "@" in value and "." in value.rsplit("@", 1)[-1]
        if method == "telegram":
            return (value.startswith("@") and len(value) >= 5) or value.startswith("https://t.me/")
        digits = "".join(character for character in compact if character.isdigit())
        return len(digits) >= 7

    @staticmethod
    def _psychologist_reply(query: str) -> SalesReply:
        lowered = query.casefold()
        if any(word in lowered for word in ("цена", "стоимость", "сколько")):
            text = (
                "Стоимость консультации в доступных данных не указана. "
                "Я не буду придумывать цену. Оставьте контакт, и менеджер "
                "уточнит актуальную стоимость и свободное время."
            )
            return SalesReply(text, "psychologist", "psychologist", needs_manager=True)
        text = (
            "Буддолог-психолог помогает со снижением стресса, развитием "
            "осознанности и работой с эмоциями. Чтобы подобрать формат "
            "консультации и время, напишите, с каким запросом Вы обращаетесь."
        )
        return SalesReply(text, "psychologist", "psychologist")

    @staticmethod
    def _contacts_reply() -> SalesReply:
        return SalesReply(
            "Связаться с командой «Свет Лотоса» можно через раздел контактов "
            "на сайте. Также можете оставить здесь имя и удобный способ связи — "
            "вопрос будет передан менеджеру.",
            "contacts",
            "contacts",
            url="https://svet-lotosa.tilda.ws/",
            needs_manager=True,
        )


_ASSISTANT = SalesAssistant()


def get_sales_assistant() -> SalesAssistant:
    return _ASSISTANT
