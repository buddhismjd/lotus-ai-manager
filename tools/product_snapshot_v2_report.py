from backend.integrations.product_snapshot_storage import snapshot_quality_counts
from backend.storage.database import initialize_database

def main() -> None:
    initialize_database()
    counts = snapshot_quality_counts()
    total = counts.get("total", 0)
    print("AI BODHI PRODUCT SNAPSHOT V2 QUALITY REPORT")
    print(f"Products: {total}")
    for key in (
        "title", "description", "brand", "sku", "price", "primary_image",
        "quantity", "category", "material", "height_cm", "availability_status",
    ):
        print(f"- {key}: {counts.get(key, 0)}/{total}")

if __name__ == "__main__":
    main()
