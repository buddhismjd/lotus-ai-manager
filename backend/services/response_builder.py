from __future__ import annotations


def build_product_response(title: str, summary: str, url: str) -> str:
    return f"""🌸 Да, у нас есть подходящий предмет.

**{title}**

{summary}

Подробнее:
{url}

Если хотите, я могу показать похожие предметы или помочь подобрать наиболее подходящий вариант.
"""


def build_tour_response(title: str, summary: str, url: str) -> str:
    return f"""🌸 Думаю, вам может подойти это путешествие.

**{title}**

{summary}

Подробнее:
{url}

Если хотите, я могу также показать похожие путешествия или помочь выбрать маршрут.
"""


def build_fallback_response() -> str:
    return (
        "🌸 Сейчас я не смог найти подходящую информацию. "
        "Попробуйте сформулировать вопрос немного иначе, "
        "или я помогу подобрать нужный товар или путешествие."
    )