from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import CORS_ALLOWED_ORIGINS, SQLITE_BUSY_TIMEOUT_MS
from backend.runtime_security import InMemoryRateLimiter, RateLimitRule

assert "https://svet-lotosa.tilda.ws" in CORS_ALLOWED_ORIGINS
print("cors_policy=OK")
assert SQLITE_BUSY_TIMEOUT_MS >= 1000
print("busy_timeout=OK")
limiter = InMemoryRateLimiter()
assert limiter.allow("diagnostic", RateLimitRule(1), now=1.0)
assert not limiter.allow("diagnostic", RateLimitRule(1), now=1.1)
print("rate_limit_contract=OK")
from backend.admin_security import require_admin_access
assert callable(require_admin_access)
print("admin_auth_contract=OK")
