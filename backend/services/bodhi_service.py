from __future__ import annotations

from backend.catalog.models import Product, Tour
from backend.catalog.repositories import ProductRepository, TourRepository
from backend.rag.dynamic_query_router import Route, route_query
from backend.services.response_builder import (
    BuiltResponse,
    build_fallback_response,
    build_product_response,
    build_tour_response,
)


def _find_product(route: Route) -> Product | None:
    """Find the routed product in the current SQLite catalog."""
    if not route.matched_title and not route.matched_url:
        return None

    for product in ProductRepository().list_all():
        if route.matched_url and product.url == route.matched_url:
            return product
        if route.matched_title and product.title == route.matched_title:
            return product

    return None


def _find_tour(route: Route) -> Tour | None:
    """Find the routed tour in the current SQLite catalog."""
    if not route.matched_title and not route.matched_url:
        return None

    for tour in TourRepository().list_all():
        if route.matched_url and tour.url == route.matched_url:
            return tour
        if route.matched_title and tour.title == route.matched_title:
            return tour

    return None


def answer_query(query: str) -> BuiltResponse:
    """
    Run the first end-to-end AI Bodhi flow.

    The function routes the query, loads the matching catalog object,
    and returns a warm user-facing response without inventing facts.
    """
    route = route_query(query)

    if route.intent == "product":
        product = _find_product(route)

        if product:
            return build_product_response(
                title=product.title,
                summary=product.description,
                url=product.url,
            )

        if route.matched_title:
            return build_product_response(
                title=route.matched_title,
                url=route.matched_url or "",
            )

        return build_fallback_response(
            "🌸 Я понял, что вы ищете товар, но пока не нашёл точную карточку."
        )

    if route.intent == "tour":
        tour = _find_tour(route)

        if tour:
            return build_tour_response(
                title=tour.title,
                summary=tour.description,
                url=tour.url,
            )

        if route.matched_title:
            return build_tour_response(
                title=route.matched_title,
                url=route.matched_url or "",
            )

        return build_fallback_response(
            "🌸 Я понял, что вы ищете путешествие, но пока не нашёл точную программу."
        )

    if route.intent == "psychologist":
        return build_fallback_response(
            "🌸 Я помогу с информацией о консультации психолога-буддолога."
        )

    if route.intent == "contacts":
        return build_fallback_response(
            "🌸 Я помогу найти контакты команды «Света Лотоса»."
        )

    if route.intent == "reviews":
        return build_fallback_response(
            "🌸 Я помогу найти отзывы участников и покупателей."
        )

    return build_fallback_response()


__all__ = ["answer_query"]
