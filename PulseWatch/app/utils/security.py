from fastapi import Depends, HTTPException, status, Header
from app.core.config import get_settings
from typing import Optional

settings = get_settings()


async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
) -> str:
    """Verify API key from request header"""

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return x_api_key
