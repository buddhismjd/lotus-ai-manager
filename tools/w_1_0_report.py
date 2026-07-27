from backend.config import CORS_ALLOWED_ORIGINS, SITE_URL


def main() -> None:
    print("AI Bodhi W-1.0 — Beta Widget Integration")
    print(f"site={SITE_URL}")
    print(f"tilda_cors={'OK' if 'https://svet-lotosa.tilda.ws' in CORS_ALLOWED_ORIGINS else 'MISSING'}")
    print("widget=/widget/embed")
    print("health=/widget/health")
    print("cards=no_descriptions, typed_buttons")
    print("network=timeout_and_retry")


if __name__ == "__main__":
    main()
