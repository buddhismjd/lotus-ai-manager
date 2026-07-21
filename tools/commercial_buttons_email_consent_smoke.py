from __future__ import annotations

from backend.sales_assistant.dialogue import NextActionType
from backend.sales_assistant.service import SalesAssistant, SalesReply


def main() -> None:
    reply = SalesAssistant()._with_dialogue(
        SalesReply(
            answer="Товар представлен в каталоге.",
            kind="product",
            topic="product",
            title="Ваджра",
            url="https://example.com/vajra",
        ),
        "product_search",
    )
    assert "https://" not in reply.answer
    assert any(item.action == NextActionType.OPEN_URL for item in reply.suggestions)
    print("SMOKE PASSED")


if __name__ == "__main__":
    main()
