from __future__ import annotations

from backend.catalog.aspect_catalog import (
    find_aspect_group,
)
from backend.catalog.models import Product, Tour
from backend.catalog.product_intelligence import analyze_product
from backend.catalog.product_profiles import get_product_profile
from backend.catalog.repositories import ProductRepository, TourRepository
from backend.rag.dynamic_query_router import (
    Route,
    detect_product_kind,
    route_query,
)
from backend.services.response_builder import (
    BuiltResponse,
    build_aspect_response,
    build_fallback_response,
    build_product_response,
    build_tour_response,
)


def _find_product(route: Route) -> Product | None:
    if not route.matched_title and not route.matched_url:
        return None

    for product in ProductRepository().list_all():
        if route.matched_url and product.url == route.matched_url:
            return product
        if route.matched_title and product.title == route.matched_title:
            return product

    return None


def _find_tour(route: Route) -> Tour | None:
    if not route.matched_title and not route.matched_url:
        return None

    for tour in TourRepository().list_all():
        if route.matched_url and tour.url == route.matched_url:
            return tour
        if route.matched_title and tour.title == route.matched_title:
            return tour

    return None


def _profile_id_from_url(url: str) -> str | None:
    import re

    match = re.search(r"/tproduct/(\d+)", url or "")
    return f"product-{match.group(1)}" if match else None


def _product_type(product: Product | None) -> str | None:
    if product is None:
        return None

    profile_id = _profile_id_from_url(product.url)

    if profile_id:
        profile = get_product_profile(profile_id)
        if profile and profile.product_type:
            return profile.product_type

    intelligence = analyze_product(
        title=product.title or "",
        description=product.description or "",
        category=getattr(product, "category", "") or "",
        sku=getattr(product, "sku", "") or "",
    )
    return intelligence.product_type


def _general_aspect_from_query(query: str) -> str | None:
    """
    Return an aspect only when the user did not request a specific
    product form.

    Examples:
        "Есть Дзамбала?" -> Дзамбала
        "Статуя Дзамбалы" -> None
    """
    if detect_product_kind(query):
        return None

    intelligence = analyze_product(title=query)

    if not intelligence.entities:
        return None

    return intelligence.entities[0]


def _aspect_grouped_products(aspect: str):
    group = find_aspect_group(aspect)

    if group is None:
        return None

    return tuple(
        (
            label,
            tuple(
                (product.title, product.url)
                for product in products
            ),
        )
        for label, products in group.by_type.items()
    )


def answer_query(query: str) -> BuiltResponse:
    """
    Route the query and build a user-facing answer.

    General aspect questions are grouped by product form.
    Specific product questions keep the single best match.
    """
    aspect = _general_aspect_from_query(query)

    if aspect:
        grouped = _aspect_grouped_products(aspect)

        if grouped:
            return build_aspect_response(
                aspect=aspect,
                grouped_products=grouped,
            )

    route = route_query(query)

    if route.intent == "product":
        product = _find_product(route)

        if product:
            return build_product_response(
                title=product.title,
                summary=product.description,
                url=product.url,
                product_type=_product_type(product),
                note=route.matched_note or "",
            )

        if route.matched_title:
            return build_product_response(
                title=route.matched_title,
                url=route.matched_url or "",
                note=route.matched_note or "",
            )

        return build_fallback_response(
            "🌸 Я понял, что Вы ищете товар, "
            "но пока не нашёл точную карточку."
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
            "🌸 Я понял, что Вы ищете путешествие, "
            "но пока не нашёл точную программу."
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
