from backend.integrations.product_raw_snapshot import load_raw_snapshot
from backend.integrations.product_snapshot_normalizer import normalize_raw_snapshot

URL = "https://svet-lotosa.tilda.ws/tproduct/296122659532-vadzhra"

def main() -> None:
    raw = load_raw_snapshot(URL)
    item = normalize_raw_snapshot(raw)
    print("=" * 72)
    print("AI BODHI PRODUCT SNAPSHOT V2 DIAGNOSTICS")
    print("=" * 72)
    print(f"UID: {item.product_uid}")
    print(f"Title: {item.title}")
    print(f"Price: {item.price}")
    print(f"SKU: {item.sku}")
    print(f"Images: {len(item.gallery)}")
    print(f"Quantity (raw): {item.quantity}")
    print(f"Category confirmed: {item.category is not None}")
    print(f"Availability confirmed: {item.availability_status is not None}")

if __name__ == "__main__":
    main()
