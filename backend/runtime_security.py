from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import (
    CHAT_RATE_LIMIT_PER_MINUTE,
    LOGS_DIR,
    RESET_RATE_LIMIT_PER_MINUTE,
    SECURITY_LOG_FILE,
)


@dataclass(frozen=True)
class RateLimitRule:
    limit: int
    window_seconds: int = 60


class InMemoryRateLimiter:
    """Small single-process limiter suitable for the current SQLite deployment."""

    def __init__(self) -> None:
        self._events: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, rule: RateLimitRule, now: float | None = None) -> bool:
        if rule.limit <= 0:
            return True
        timestamp = time.monotonic() if now is None else now
        cutoff = timestamp - rule.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= rule.limit:
                return False
            events.append(timestamp)
            return True

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


rate_limiter = InMemoryRateLimiter()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def write_security_event(event: str, request: Request, **details: object) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    path = Path(SECURITY_LOG_FILE)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "path": request.url.path,
        "method": request.method,
        "client_ip": _client_ip(request),
        "details": details,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


class PublicApiRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        rule: RateLimitRule | None = None
        scope = ""
        if path == "/api/sales/chat" and request.method == "POST":
            rule = RateLimitRule(CHAT_RATE_LIMIT_PER_MINUTE)
            scope = "sales_chat"
        elif path == "/api/sales/reset" and request.method == "POST":
            rule = RateLimitRule(RESET_RATE_LIMIT_PER_MINUTE)
            scope = "sales_reset"

        if rule is not None:
            key = f"{scope}:{_client_ip(request)}"
            if not rate_limiter.allow(key, rule):
                write_security_event("rate_limit_exceeded", request, scope=scope)
                return JSONResponse(
                    status_code=429,
                    content={
                        "status": "rate_limited",
                        "error": {
                            "code": "rate_limit_exceeded",
                            "message": "Слишком много запросов. Повторите попытку через минуту.",
                        },
                    },
                    headers={"Retry-After": "60"},
                )
        return await call_next(request)
