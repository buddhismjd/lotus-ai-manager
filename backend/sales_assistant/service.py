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
from backend.sales_assistant.selection_page import build_selection_url
from backend.sales_assistant.product_selection import (
    ProductSelectionRequest,
    ProductSelectionResult,
    ProductSelectionService,
    parse_product_selection_request,
)
from backend.sales_assistant.state import DialogueStage, DialogueState, DialogueStateStore
from backend.sales_assistant.strategy import choose_strategy
from backend.sales_assistant.tone import (
    TONE,
    email_request_for_topic,
    email_saved_for_topic,
    warm_missing_date,
    warm_missing_price,
)
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
        self._product_selection = ProductSelectionService()

    def reset(self, session_id: str) -> None:
        self._states.reset(session_id)

    def reply(self, message: str, session_id: str = "default") -> SalesReply:
        query = message.strip()
        if not query:
            return SalesReply(TONE.empty_request, "empty", "unknown")

        state = self._states.get(session_id)

        if state.stage in {
            DialogueStage.ARTISAN_SOCIAL_METHOD,
            DialogueStage.ARTISAN_SOCIAL_VALUE,
            DialogueStage.ARTISAN_EMAIL,
        }:
            return self._handle_artisan_selection(query, state)

        if state.stage == DialogueStage.EMAIL_VALUE:
            return self._handle_email_followup(query, state)

        if state.stage != DialogueStage.DISCOVERY:
            return self._handle_lead_capture(query, state)

        if self._starts_artisan_selection(query):
            state.start_artisan_selection()
            return SalesReply(
                answer=(
                    "С радостью уточню актуальное наличие у мастеров и помогу подготовить "
                    "персональную подборку. Выберите, пожалуйста, удобный способ связи: "
                    "Telegram или WhatsApp."
                ),
                kind="artisan_selection",
                topic="product",
                next_action=NextActionType.ARTISAN_SELECTION,
                suggestions=(
                    DialogueSuggestion(NextActionType.ARTISAN_SELECTION, "Telegram", "Telegram"),
                    DialogueSuggestion(NextActionType.ARTISAN_SELECTION, "WhatsApp", "WhatsApp"),
                ),
                dialogue_stage=state.stage.value,
            )

        if self._starts_email_followup(query):
            state.start_email_followup()
            current_topic = self._state_topic(state)
            return SalesReply(
                answer=email_request_for_topic(current_topic),
                kind="email_capture",
                topic=current_topic,
                next_action=NextActionType.EMAIL_FOLLOWUP,
                dialogue_stage=state.stage.value,
            )

        if self._starts_lead_capture(query):
            state.start_lead_capture()
            return SalesReply(
                answer=(
                    "С удовольствием помогу передать Ваш интерес менеджеру. "
                    "Как я могу к Вам обращаться?"
                ),
                kind="lead_capture",
                topic=self._state_topic(state),
                next_action=NextActionType.ASK_NAME,
                dialogue_stage=state.stage.value,
            )

        selection_request = parse_product_selection_request(query)
        if selection_request is not None:
            selection_result = self._product_selection.select(selection_request)
            state.remember_product_selection(
                category=selection_request.category,
                aspect=selection_request.aspect,
                height_min_cm=selection_request.height_min_cm,
                height_max_cm=selection_request.height_max_cm,
            )
            state.last_query = query
            if len(selection_result.products) == 1:
                state.active_title = selection_result.products[0].title
                state.active_url = selection_result.products[0].url
            else:
                state.active_title = selection_request.aspect or selection_request.category_label
                state.active_url = None
            return self._product_selection_reply(selection_result)

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
                if len(product_items) == 1:
                    state.active_title = product_items[0].title
                    state.active_url = product_items[0].url
                else:
                    state.active_title = None
                    state.active_url = None
                answer = (
                    f"Нашла {len(product_items)} подходящих "
                    + (
                        "товар."
                        if len(product_items) == 1
                        else "товара."
                        if len(product_items) < 5
                        else "товаров."
                    )
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

        if self._asks_for_tour_selection(query) and state.candidate_tour_ids:
            state.last_query = query
            state.topic = "tour"
            state.goal = "choose_tour"
            return self._tour_selection_reply(state)

        country = detect_country(query)
        normalised_query = self._normalise(query)
        standalone_country = bool(
            country and normalised_query == self._normalise(country)
        )
        explicit_country = country is not None and self._normalise(country) in normalised_query
        country_collection_request = explicit_country and (
            standalone_country or any(
            marker in normalised_query
            for marker in (
                "возите",
                "есть поезд",
                "есть тур",
                "туры в",
                "поездки в",
                "путешествия в",
                "что есть",
                "покажите",
                "покажи",
            )
        )
        )
        if (
            (topic == "tour" or standalone_country)
            and country_collection_request
            and decision.month is None
            and decision.strategy not in {"tour_price", "tour_date"}
        ):
            tour_items = build_tour_collection(query)
            state.last_query = query
            state.topic = "tour"
            if tour_items:
                planned_only = all(item.status == "planned" for item in tour_items)
                answer = (
                    f"По направлению «{country}» опубликованных программ пока нет, "
                    "но готовится следующее путешествие:"
                    if planned_only
                    else f"Нашла путешествия по направлению «{country}»:"
                )
                return self._with_dialogue(
                    SalesReply(
                        answer=answer,
                        kind="tour_collection",
                        topic="tour",
                        items=tuple(item.to_dict() for item in tour_items),
                        needs_manager=planned_only,
                    ),
                    "tour_list",
                )
            return self._with_dialogue(
                SalesReply(
                    answer=(
                        "Сейчас я не нашла опубликованных или планируемых "
                        f"путешествий по направлению «{country}»."
                    ),
                    kind="tour_collection",
                    topic="tour",
                ),
                "tour_list",
            )

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
            link_suggestions = tuple(
                DialogueSuggestion(
                    NextActionType.OPEN_URL,
                    f"Открыть: {tour.title}",
                    url=tour.url,
                )
                for tour in tours
                if tour.url
            )
            return SalesReply(
                answer=format_tour_list(tours, month=decision.month, limit=None),
                kind="tour_list",
                topic="tour",
                needs_manager=plan.requires_manager,
                next_action=plan.next_action,
                suggestions=link_suggestions + plan.suggestions,
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
        elif response.kind in {"product", "psychologist"}:
            state.active_title = response.title or (
                "Консультация психолога-буддолога"
                if response.kind == "psychologist"
                else state.active_title
            )
            state.active_url = response.url

        state.last_query = query
        if resolved_topic != "unknown":
            state.topic = resolved_topic

        if decision.strategy == "tour_price" and response.kind == "tour":
            tour = self._find_structured_tour(response.title, response.url)
            if tour is None or tour.price is None:
                title = response.title or (tour.title if tour else "этот тур")
                reply = SalesReply(
                    answer=(
                        warm_missing_price(title)
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
                "Хорошо, оформление заявки остановлено. Буду рада продолжить беседу, когда Вам будет удобно.",
                "lead_cancelled",
                self._state_topic(state),
                dialogue_stage=state.stage.value,
            )

        if state.stage == DialogueStage.LEAD_NAME:
            name = query.strip()
            if len(name) < 2 or len(name) > 80:
                return SalesReply(
                    "Подскажите, пожалуйста, как я могу к Вам обращаться.",
                    "lead_capture",
                    self._state_topic(state),
                    next_action=NextActionType.ASK_NAME,
                    dialogue_stage=state.stage.value,
                )
            state.lead.name = name
            state.stage = DialogueStage.LEAD_CONTACT_METHOD
            return SalesReply(
                "Благодарю Вас. Какой способ связи будет наиболее удобен: Telegram, WhatsApp, телефон или email?",
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
                    "Пожалуйста, выберите удобный способ связи: Telegram, WhatsApp, телефон или email.",
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
                    "Похоже, в контакте есть неточность. Пожалуйста, проверьте его и отправьте ещё раз.",
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
            answer = "Благодарю Вас. Заявка сохранена и будет бережно передана менеджеру."
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
            "Буду рада продолжить. Что ещё Вас интересует?",
            "lead_reset",
            self._state_topic(state),
            dialogue_stage=state.stage.value,
        )

    def _handle_email_followup(self, query: str, state: DialogueState) -> SalesReply:
        if self._cancels_lead_capture(query):
            state.stage = DialogueStage.DISCOVERY
            state.goal = None
            state.lead.clear()
            return SalesReply(
                "Хорошо, email не сохраняю. Буду рада продолжить беседу.",
                "email_cancelled",
                self._state_topic(state),
                dialogue_stage=state.stage.value,
            )

        email = query.strip()
        if not self._valid_contact("email", email):
            return SalesReply(
                TONE.email_invalid,
                "email_capture",
                self._state_topic(state),
                next_action=NextActionType.EMAIL_FOLLOWUP,
                dialogue_stage=state.stage.value,
            )

        interest = state.lead.interest
        summary = state.lead.conversation_summary or state.last_query
        subscription_topic = state.lead.subscription_topic or "requested_information"
        consent_text = state.lead.consent_text or (
            "Согласие получить информацию по текущему запросу."
        )
        current_topic = self._state_topic(state)
        saved = self._leads.save(
            name=state.lead.name or "Посетитель сайта",
            contact_method="email",
            contact_value=email,
            interest=interest,
            comment=(
                f"subscription_topic={subscription_topic}; "
                f"consent_text={consent_text}; "
                f"interest_category={current_topic}; "
                f"interest_title={interest or 'не указан'}; "
                f"context={summary or 'не указан'}"
            ),
        )
        state.stage = DialogueStage.DISCOVERY
        state.goal = None
        state.lead.clear()
        answer = email_saved_for_topic(current_topic)
        if interest and interest not in {"unknown", "contacts"}:
            answer += f" Тема интереса: «{interest}»."
        return SalesReply(
            answer=answer,
            kind="email_saved",
            topic=self._state_topic(state),
            next_action=NextActionType.EMAIL_SAVED,
            dialogue_stage=DialogueStage.EMAIL_VALUE.value,
            lead_id=saved.id,
        )

    def _product_selection_reply(
        self,
        result: ProductSelectionResult,
    ) -> SalesReply:
        request = result.request
        subject = request.category_label
        if request.aspect:
            subject += f" {request.aspect}"
        if request.height_label:
            subject += f" высотой {request.height_label}"

        suggestions: list[DialogueSuggestion] = []
        if result.products:
            count = len(result.products)
            answer = (
                f"С радостью подготовила точную подборку: {subject}. "
                f"В неё вошло {count} подходящих позиций. "
                "Откройте подборку, чтобы спокойно посмотреть каждый вариант."
            )
            suggestions.append(
                DialogueSuggestion(
                    NextActionType.OPEN_URL,
                    "Открыть точную подборку",
                    url=build_selection_url(request),
                )
            )
        else:
            answer = (
                f"В опубликованном каталоге сейчас нет точных совпадений для запроса: {subject}. "
                "Я не стану предлагать неподходящие варианты. Можно уточнить актуальное "
                "наличие у мастеров и подготовить персональную подборку."
            )

        suggestions.append(
            DialogueSuggestion(
                NextActionType.ARTISAN_SELECTION,
                "Уточнить наличие у мастеров",
                "Хочу персональную подборку от мастеров",
            )
        )
        tail = (
            "\n\nКроме позиций на сайте, мы можем уточнить актуальное наличие у мастеров "
            "и прислать Вам персональную подборку. Для этого понадобятся контакт "
            "в Telegram или WhatsApp и email."
        )
        product_items = build_product_collection(subject, result.products)
        return SalesReply(
            answer=answer + tail,
            kind="product_selection",
            topic="product",
            title=request.aspect or request.category_label.capitalize(),
            next_action=NextActionType.ARTISAN_SELECTION,
            suggestions=tuple(suggestions),
            items=tuple(item.to_dict() for item in product_items),
        )

    def _handle_artisan_selection(
        self,
        query: str,
        state: DialogueState,
    ) -> SalesReply:
        if self._cancels_lead_capture(query):
            state.stage = DialogueStage.DISCOVERY
            state.goal = None
            state.lead.clear()
            return SalesReply(
                "Хорошо, запрос на персональную подборку остановлен. Буду рада продолжить беседу.",
                "artisan_cancelled",
                "product",
                dialogue_stage=state.stage.value,
            )

        if state.stage == DialogueStage.ARTISAN_SOCIAL_METHOD:
            method = self._parse_social_method(query)
            if method is None:
                return SalesReply(
                    "Выберите, пожалуйста, Telegram или WhatsApp.",
                    "artisan_selection",
                    "product",
                    next_action=NextActionType.ARTISAN_SELECTION,
                    suggestions=(
                        DialogueSuggestion(NextActionType.ARTISAN_SELECTION, "Telegram", "Telegram"),
                        DialogueSuggestion(NextActionType.ARTISAN_SELECTION, "WhatsApp", "WhatsApp"),
                    ),
                    dialogue_stage=state.stage.value,
                )
            state.lead.social_channel = method
            state.stage = DialogueStage.ARTISAN_SOCIAL_VALUE
            label = "Ваш Telegram, например @username" if method == "telegram" else "номер WhatsApp с кодом страны"
            return SalesReply(
                f"Напишите, пожалуйста, {label}.",
                "artisan_selection",
                "product",
                next_action=NextActionType.ARTISAN_SELECTION,
                dialogue_stage=state.stage.value,
            )

        if state.stage == DialogueStage.ARTISAN_SOCIAL_VALUE:
            method = state.lead.social_channel or "telegram"
            value = query.strip()
            if not self._valid_contact(method, value):
                return SalesReply(
                    "Похоже, в контакте есть неточность. Пожалуйста, проверьте его и отправьте ещё раз.",
                    "artisan_selection",
                    "product",
                    next_action=NextActionType.ARTISAN_SELECTION,
                    dialogue_stage=state.stage.value,
                )
            state.lead.social_contact = value
            state.stage = DialogueStage.ARTISAN_EMAIL
            return SalesReply(
                "Благодарю Вас. Теперь напишите, пожалуйста, email, на который мы сможем прислать подборку.",
                "artisan_selection",
                "product",
                next_action=NextActionType.ARTISAN_SELECTION,
                dialogue_stage=state.stage.value,
            )

        if state.stage == DialogueStage.ARTISAN_EMAIL:
            email = query.strip()
            if not self._valid_contact("email", email):
                return SalesReply(
                    TONE.email_invalid,
                    "artisan_selection",
                    "product",
                    next_action=NextActionType.ARTISAN_SELECTION,
                    dialogue_stage=state.stage.value,
                )
            saved = self._leads.save_artisan_selection(
                social_channel=state.lead.social_channel or "telegram",
                social_contact=state.lead.social_contact or "",
                email=email,
                interest=state.lead.interest,
                selection_category=state.lead.selection_category,
                selection_aspect=state.lead.selection_aspect,
                requested_height_min_cm=state.lead.requested_height_min_cm,
                requested_height_max_cm=state.lead.requested_height_max_cm,
                consent_text=state.lead.consent_text or "",
                conversation_summary=state.last_query,
            )
            state.stage = DialogueStage.DISCOVERY
            state.goal = None
            state.lead.clear()
            return SalesReply(
                "Благодарю Вас. Контакты и параметры подбора сохранены. Мы уточним актуальное наличие у мастеров и бережно пришлём Вам подходящие варианты.",
                "artisan_saved",
                "product",
                needs_manager=True,
                next_action=NextActionType.LEAD_SAVED,
                dialogue_stage=DialogueStage.ARTISAN_EMAIL.value,
                lead_id=saved.id,
            )

        state.stage = DialogueStage.DISCOVERY
        return SalesReply(
            "Буду рада продолжить. Что ещё Вас интересует?",
            "artisan_reset",
            "product",
            dialogue_stage=state.stage.value,
        )

    def _tour_selection_reply(self, state: DialogueState) -> SalesReply:
        tours = self._candidate_tours(state)
        if not tours:
            return self._with_dialogue(
                SalesReply(
                    answer=(
                        "Мне не удалось сохранить предыдущие варианты. "
                        "Напишите, пожалуйста, какое направление Вас заинтересовало, и я вновь покажу подходящие путешествия."
                    ),
                    kind="fallback",
                    topic="tour",
                    needs_manager=False,
                ),
                "tour_list",
            )

        cards: list[str] = ["С радостью помогу внимательнее рассмотреть найденные путешествия:"]
        for tour in tours[:4]:
            facts = [f"🗻 {tour.title}"]
            if tour.schedule and tour.schedule.source_text:
                facts.append(f"📅 {tour.schedule.source_text}")
            if tour.duration_days:
                facts.append(f"⏱ {tour.duration_days} дней")
            if tour.countries:
                facts.append(f"📍 {', '.join(tour.countries)}")
            cards.append("\n".join(facts))

        cards.append("Выберите путешествие, о котором Вам хотелось бы узнать подробнее.")
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
                    warm_missing_price(tour.title)
                ),
                kind="tour_price",
                topic="tour",
                title=tour.title,
                url=tour.url,
                needs_manager=True,
            )
        return SalesReply(
            answer=f"Стоимость путешествия «{tour.title}» составляет {tour.price} {tour.currency}.",
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
                warm_missing_date(tour.title)
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
        suggestions = list(plan.suggestions)
        if reply.url and reply.topic in {"tour", "product"}:
            label = "Открыть страницу тура" if reply.topic == "tour" else "Открыть товар"
            suggestions.insert(
                0,
                DialogueSuggestion(
                    NextActionType.OPEN_URL,
                    label,
                    url=reply.url,
                ),
            )
        return SalesReply(
            answer=reply.answer,
            kind=reply.kind,
            topic=reply.topic,
            title=reply.title,
            url=reply.url,
            needs_manager=plan.requires_manager,
            next_action=plan.next_action,
            suggestions=tuple(suggestions),
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
    def _starts_artisan_selection(cls, query: str) -> bool:
        lowered = cls._normalise(query)
        return any(
            marker in lowered
            for marker in (
                "персональную подборку",
                "подборку от мастеров",
                "наличие у мастеров",
                "уточнить у мастеров",
            )
        )

    @classmethod
    def _parse_social_method(cls, query: str) -> str | None:
        lowered = cls._normalise(query)
        if "telegram" in lowered or "телеграм" in lowered:
            return "telegram"
        if "whatsapp" in lowered or "ватсап" in lowered or "вотсап" in lowered:
            return "whatsapp"
        return None

    @classmethod
    def _starts_email_followup(cls, query: str) -> bool:
        lowered = cls._normalise(query)
        markers = (
            "отправьте информацию на email",
            "отправить информацию на email",
            "отправьте на email",
            "отправьте на почту",
            "пришлите на email",
            "пришлите на почту",
            "хочу получить на email",
            "новых турах на email",
            "новых товарах на email",
            "консультации на email",
            "информацию на email",
            "информацию о консультации на email",
            "информацию на почту",
        )
        return any(marker in lowered for marker in markers)

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
                "Стоимость консультации пока не указана на сайте. Я не стану вводить Вас в заблуждение. "
                "Могу сохранить Ваш интерес, чтобы менеджер уточнил актуальную стоимость и свободное время."
            )
            return SalesReply(text, "psychologist", "psychologist", needs_manager=True)
        text = (
            "Консультация психолога-буддолога может поддержать в работе со стрессом, эмоциями и развитии осознанности. "
            "Если Вам откликается такой формат, расскажите, пожалуйста, с каким вопросом Вы хотели бы обратиться."
        )
        return SalesReply(text, "psychologist", "psychologist")

    @staticmethod
    def _contacts_reply() -> SalesReply:
        return SalesReply(
            "Связаться с командой «Свет Лотоса» можно через раздел контактов на сайте. "
            "При желании Вы также можете оставить здесь имя и удобный способ связи — мы бережно передадим Ваш вопрос менеджеру.",
            "contacts",
            "contacts",
            url="https://svet-lotosa.tilda.ws/",
            needs_manager=True,
        )


_ASSISTANT = SalesAssistant()


def get_sales_assistant() -> SalesAssistant:
    return _ASSISTANT
