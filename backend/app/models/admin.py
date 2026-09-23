"""Admin collection entity models and enums."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class AdminRole(str, Enum):
    PRESIDENT = "PRESIDENT"
    ADMIN = "ADMIN"


class AdminStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class AdminModel(BaseModel):
    uid: str
    name: str
    email: str
    role: AdminRole = AdminRole.ADMIN
    status: AdminStatus = AdminStatus.ACTIVE
    permissions: List[str] = Field(default_factory=lambda: ["mark_attendance", "view_reports"])
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
