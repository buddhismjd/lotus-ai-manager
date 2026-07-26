from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product
from backend.tours.collection_builder import detect_country

print("tibet_direction:", "OK" if detect_country("В Тибет возите?") == "Тибет" else "FAIL")
item = build_product_collection("Есть ли ваджра?", [Product(id="v", title="Ваджра", url="https://svet-lotosa.tilda.ws/tproduct/1-vadzhra")])[0]
print("product_image_fallback:", "OK" if item.image_url else "FAIL")
