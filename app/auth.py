import hmac
import os

from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


load_dotenv(dotenv_path=".env")


api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def require_api_key(
    provided_key: str | None = Security(
        api_key_header
    )
) -> str:

    expected_key = os.getenv(
        "APP_API_KEY"
    )

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application API key is not configured"
        )

    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )

    if not hmac.compare_digest(
        provided_key,
        expected_key
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return provided_key
