from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, Query, Request

from backend.config import ADMIN_TOKEN
from backend.runtime_security import write_security_event


def require_admin_access(
    request: Request,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    admin_token: str | None = Query(default=None),
) -> None:
    supplied = x_admin_token or admin_token or ""
    configured = ADMIN_TOKEN or ""
    if not configured or not hmac.compare_digest(supplied, configured):
        write_security_event("admin_access_denied", request)
        raise HTTPException(status_code=401, detail="Admin access denied")
