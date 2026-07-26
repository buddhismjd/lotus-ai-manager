from backend.catalog.repositories import TourRepository


def main() -> None:
    tours = TourRepository().list_all()
    priced = [tour for tour in tours if tour.price is not None]
    print("Tour Price Diagnostics")
    print(f"Tours: {len(tours)}")
    print(f"Tours with price: {len(priced)}")
    for tour in priced:
        print(f"OK | {tour.title} | {tour.price} {tour.currency}")


if __name__ == "__main__":
    main()
