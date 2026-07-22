from __future__ import annotations

from backend.tours.collection_builder import is_country_collection_query


def main() -> int:
    checks = {
        "standalone_nepal": is_country_collection_query("Непал"),
        "nepal_collection": is_country_collection_query("Покажите туры в Непал"),
        "exact_kailas_not_country_collection": not is_country_collection_query("Есть тур на Кайлас?"),
    }
    for name, passed in checks.items():
        print(f"{name}: {'OK' if passed else 'FAIL'}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
