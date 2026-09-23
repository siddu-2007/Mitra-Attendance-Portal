"""Authentication request and response schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Unified login payload accepting either Roll Number or College Email."""
    identifier: str = Field(..., min_length=2, description="Roll Number (e.g. 24PA1A4511) or College Email")
    passkey: Optional[str] = Field(None, description="Optional passkey / password for authentication")


class LoginResponse(BaseModel):
    """Successful login response containing access role, token, and user profile."""
    role: str = Field(..., description="Access clearance: PRESIDENT, ADMIN, or STUDENT")
    token: str = Field(..., description="Bearer authorization token")
    portalRedirect: str = Field(..., description="Target portal route: /dashboard or /student")
    user: Dict[str, Any] = Field(..., description="Resolved user profile attributes")
