from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dataclasses import dataclass

from backend.sales_assistant.service import SalesAssistant


@dataclass(frozen=True)
class _Saved:
    id: int = 110


class _MemoryLeadRepository:
    def __init__(self) -> None:
        self.summary = ""

    def save_handoff(self, **kwargs):
        self.summary = kwargs["manager_summary"]
        return _Saved()


def main() -> None:
    assistant = SalesAssistant()
    repository = _MemoryLeadRepository()
    assistant._leads = repository  # type: ignore[assignment]
    session_id = "cb-1.1.0-smoke"

    messages = (
        "Можно забронировать место в туре в Непал?",
        "Анна",
        "Telegram",
        "@anna_lotus",
        "anna@example.com",
    )
    reply = None
    for message in messages:
        reply = assistant.reply(message, session_id)

    assert reply is not None
    assert reply.kind == "handoff_saved"
    assert reply.lead_id == 110
    assert repository.summary
    print("conversation_handoff_smoke=OK")
    print(repository.summary)


if __name__ == "__main__":
    main()
