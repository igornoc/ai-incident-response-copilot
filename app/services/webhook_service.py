import hmac
import os

from dotenv import load_dotenv


load_dotenv(dotenv_path=".env")


def verify_webhook_secret(
    provided_secret: str | None
) -> bool:

    expected_secret = os.getenv(
        "WEBHOOK_SECRET"
    )

    if not expected_secret:
        return False

    if not provided_secret:
        return False

    return hmac.compare_digest(
        provided_secret,
        expected_secret
    )
