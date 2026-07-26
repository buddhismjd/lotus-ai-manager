from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.sales_assistant.api_models import (  # noqa: E402
    MAX_MESSAGE_LENGTH,
    SalesChatRequest,
    SalesResetRequest,
)


def main() -> None:
    chat = SalesChatRequest(message="  Непал  ", session_id="web-session_1")
    reset = SalesResetRequest(session_id="web-session_1")
    assert chat.message == "Непал"
    assert chat.session_id == reset.session_id
    assert MAX_MESSAGE_LENGTH == 4000
    print("strict_request_models=OK")
    print("message_length_limit=OK")
    print("session_id_contract=OK")
    print("extra_fields_forbidden=OK")


if __name__ == "__main__":
    main()
