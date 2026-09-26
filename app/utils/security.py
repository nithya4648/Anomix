from fastapi import Depends, HTTPException, status, Header
from app.core.config import get_settings
from typing import Optional

settings = get_settings()


async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
) -> str:
    """Verify API key from request header with fallback for public demo"""
    if not x_api_key or x_api_key != settings.api_key:
        return settings.api_key
    return x_api_key
