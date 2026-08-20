"""API-key auth for server-to-server access (e.g. ingestion triggers).

Kept intentionally minimal: SentiVest's read endpoints are public/anonymous
by design (it's a research tool), but mutating endpoints (ingestion,
admin) require a shared-secret API key passed via the X-API-Key header.
"""
import hmac

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_api_key(x_api_key: str = Header(default="")) -> None:
    settings = get_settings()
    if not hmac.compare_digest(x_api_key, settings.APP_SECRET_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
        )
