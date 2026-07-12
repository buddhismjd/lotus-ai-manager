from backend.services.bodhi_service import answer_query
from backend.sales_assistant.formatter import format_sales_response


def main() -> None:
    response = format_sales_response(answer_query("На Кайлас возите?"))
    forbidden = ("Путешествия\nМагазин", "План маршрута", "🗓️ День 0", "**")
    print("=" * 72)
    print("AI BODHI SALES RESPONSE FORMATTER DIAGNOSTICS")
    print("=" * 72)
    print(f"Kind: {response.kind}")
    print(f"Title: {response.title}")
    print(f"Length: {len(response.text)}")
    print(f"Clean: {not any(item in response.text for item in forbidden)}")
    print("-" * 72)
    print(response.text)


if __name__ == "__main__":
    main()
