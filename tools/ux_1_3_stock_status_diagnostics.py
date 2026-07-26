from backend.integrations.tilda_store_api import _extract_availability_status


def main() -> None:
    assert _extract_availability_status({"title": "Статуя", "html": "Фильтр: В наличии"}) is None
    assert _extract_availability_status({"title": "Статуя", "quantity": 0}) == "Нет в наличии"
    print("UX-1.3 diagnostic: PASS")
    print("Generic Tilda UI text cannot create a false in-stock status.")
    print("Zero quantity is rendered as 'Нет в наличии'.")


if __name__ == "__main__":
    main()
