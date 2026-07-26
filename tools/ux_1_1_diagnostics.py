from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.rag.dynamic_query_router import route_query
from backend.tours.collection_builder import clean_tour_description


def main() -> int:
    route = route_query("Колокольчик имеется?")
    cleaned = clean_tour_description(
        "Путешествия\nМагазин\nОтзывы\nПаломнический тур в Тибет."
    )
    print(f"route={route.intent} reason={route.reason}")
    print(f"cleaned_description={cleaned}")
    return 0 if route.intent == "product" and cleaned == "Паломнический тур в Тибет." else 1


if __name__ == "__main__":
    raise SystemExit(main())
