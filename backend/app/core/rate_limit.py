"""Rate Limiting Configuration for FastAPI endpoints."""

from typing import Callable
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.logging import logger


def get_client_identifier(request: Request) -> str:
    """Extract client IP or authenticated admin UID for rate limiting."""
    # If admin UID is available in request state, rate-limit per user
    admin_uid = getattr(request.state, "admin_uid", None)
    if admin_uid:
        return f"admin:{admin_uid}"
    # Fallback to remote IP address
    return get_remote_address(request)


# Global Limiter instance
limiter = Limiter(key_func=get_client_identifier, default_limits=["120/minute"])
