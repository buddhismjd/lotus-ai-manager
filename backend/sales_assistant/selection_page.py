from __future__ import annotations

from html import escape
from urllib.parse import urlencode

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from backend.catalog.models import Product
from backend.catalog.collection_builder import _price
from backend.sales_assistant.product_selection import (
    ProductSelectionRequest,
    ProductSelectionService,
)

router = APIRouter(tags=["product-selection"])

_STYLE = """
<style>
:root{color-scheme:light}
*{box-sizing:border-box}
body{font-family:Arial,sans-serif;background:#f7f3ff;color:#2d2440;margin:0;padding:28px 16px}
.container{max-width:1180px;margin:auto}
.hero,.card,.artisan{background:#fff;border:1px solid #e7def8;border-radius:20px;box-shadow:0 7px 25px rgba(70,42,120,.06)}
.hero{padding:26px;margin-bottom:20px}.hero h1{margin:0 0 12px;font-size:clamp(28px,4vw,42px)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px}
.card{overflow:hidden;display:flex;flex-direction:column;min-height:100%}
.product-image{width:100%;aspect-ratio:1/1;object-fit:cover;background:#f0ebfa}
.image-missing{aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;background:#f0ebfa;color:#786f88;text-align:center;padding:16px}
.card-body{padding:18px;display:flex;flex-direction:column;flex:1}
.title{font-size:20px;font-weight:700;margin-bottom:12px;line-height:1.2}
.meta{line-height:1.65;color:#5d536c}.meta-row{margin-bottom:4px}.status{font-weight:700;color:#3d3561}
.button{display:inline-block;margin-top:auto;padding:11px 16px;border-radius:999px;background:#6847d9;color:#fff;text-decoration:none;text-align:center;font-weight:700}
.secondary{background:#ede7ff;color:#4b358d}.empty{padding:28px;text-align:center}.muted{color:#786f88}
.artisan{margin-top:20px;padding:22px}.artisan p{font-size:18px;line-height:1.55;margin:0 0 14px}
.actions{display:flex;gap:10px;flex-wrap:wrap}.actions .button{margin-top:0}
</style>
"""


def build_selection_url(request: ProductSelectionRequest) -> str:
    params: dict[str, str] = {"category": request.category}
    if request.aspect:
        params["aspect"] = request.aspect
    if request.height_min_cm is not None:
        params["height_min_cm"] = f"{request.height_min_cm:g}"
    if request.height_max_cm is not None:
        params["height_max_cm"] = f"{request.height_max_cm:g}"
    return f"/api/sales/product-selection?{urlencode(params)}"


def _render_product_card(
    product: Product,
    service: ProductSelectionService,
) -> str:
    del service  # Rendering is governed by the commercial card contract.
    price = _price(product.price, product.currency) or "Цена уточняется"
    status = product.availability_status or "Наличие уточняется"
    if product.image_url:
        image = (
            f"<img class='product-image' src='{escape(product.image_url)}' "
            f"alt='{escape(product.title)}' loading='lazy'>"
        )
    else:
        image = ""

    return (
        "<article class='card'>"
        f"{image}"
        "<div class='card-body'>"
        f"<div class='title'>{escape(product.title)}</div>"
        "<div class='meta'>"
        f"<div class='meta-row'>{escape(price)}</div>"
        f"<div class='meta-row status'>{escape(status)}</div>"
        "</div>"
        f"<a class='button' href='{escape(product.url)}' target='_blank' rel='noopener noreferrer'>Открыть товар</a>"
        "</div></article>"
    )


@router.get("/product-selection", response_class=HTMLResponse)
def product_selection_page(
    category: str = Query(..., pattern="^(statue|thangka)$"),
    aspect: str | None = None,
    height_min_cm: float | None = Query(None, ge=0.1, le=500),
    height_max_cm: float | None = Query(None, ge=0.1, le=500),
) -> str:
    if (height_min_cm is None) != (height_max_cm is None):
        return HTMLResponse("Некорректно задан диапазон высоты.", status_code=400)
    if height_min_cm is not None and height_max_cm is not None and height_min_cm > height_max_cm:
        return HTMLResponse("Минимальная высота не может быть больше максимальной.", status_code=400)

    request = ProductSelectionRequest(
        category=category,
        category_label="статуи" if category == "statue" else "тханки",
        aspect=(aspect or "").strip() or None,
        height_min_cm=height_min_cm,
        height_max_cm=height_max_cm,
    )
    service = ProductSelectionService()
    result = service.select(request)

    subject = request.category_label
    if request.aspect:
        subject += f" {request.aspect}"
    if request.height_label:
        subject += f" высотой {request.height_label}"

    cards = [_render_product_card(product, service) for product in result.products]
    if cards:
        content = f"<div class='grid'>{''.join(cards)}</div>"
    else:
        content = (
            "<div class='card empty'>"
            "<p>В опубликованном каталоге сейчас нет точных совпадений.</p>"
            "<p class='muted'>Можно вернуться в чат и запросить персональную подборку.</p>"
            "</div>"
        )

    artisan_text = (
        "Мы также можем уточнить актуальное наличие у мастеров Тибета и Непала "
        "и прислать Вам персональную подборку."
    )

    return (
        "<!doctype html><html lang='ru'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Подборка: {escape(subject)}</title>{_STYLE}</head><body><main class='container'>"
        "<section class='hero'>"
        f"<h1>Подборка: {escape(subject)}</h1>"
        f"<p>Для Вас подобраны {len(result.products)} позиций, соответствующих запросу.</p>"
        "<a class='button secondary' href='/chat-ui'>Вернуться в чат</a>"
        "</section>"
        f"{content}"
        "<section class='artisan'>"
        f"<p>{escape(artisan_text)}</p>"
        "<div class='actions'>"
        "<a class='button' href='/chat-ui?message=Хочу%20получить%20персональную%20подборку'>Да, хочу получить подборку</a>"
        "<a class='button secondary' href='/chat-ui'>Пока посмотрю товары на сайте</a>"
        "</div></section>"
        "</main></body></html>"
    )


__all__ = ["router", "build_selection_url", "_render_product_card"]
