from __future__ import annotations

import re
from functools import lru_cache
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

router = APIRouter()
_IMAGE_PATTERNS = (
    re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', re.I),
)
_ALLOWED_HOSTS = {"svet-lotosa.tilda.ws"}

@lru_cache(maxsize=256)
def resolve_page_image(source: str) -> str | None:
    parsed = urlparse(source)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        return None
    request = Request(source, headers={"User-Agent": "Lotus-AI-Manager/1.0"})
    with urlopen(request, timeout=8) as response:
        html = response.read(1_500_000).decode("utf-8", errors="ignore")
    for pattern in _IMAGE_PATTERNS:
        match = pattern.search(html)
        if match:
            image = match.group(1).replace("&amp;", "&").strip()
            if image.startswith("https://"):
                return image
    return None

@router.get("/page-image")
def page_image(source: str = Query(...)) -> RedirectResponse:
    try:
        image = resolve_page_image(source)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Page image unavailable") from exc
    if not image:
        raise HTTPException(status_code=404, detail="Page image unavailable")
    return RedirectResponse(image, status_code=307)


# Backward-compatible product endpoint used by existing cards.
resolve_product_image = resolve_page_image


@router.get("/product-image")
def product_image(source: str = Query(...)) -> RedirectResponse:
    return page_image(source)
