"""API Key authentication dependency."""

from __future__ import annotations

from fastapi import Header, HTTPException

from .config import Settings


def verify_api_key(settings: Settings, x_api_key: str = Header(...)) -> None:
    """Raise 401 if *x_api_key* does not match ``APP_API_KEY``."""
    if x_api_key != settings.app_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
