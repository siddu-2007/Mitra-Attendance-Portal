"""Member collection entity models and enums."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MemberStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class MemberModel(BaseModel):
    memberId: str
    name: str
    email: str
    phone: Optional[str] = None
    departmentId: str
    academicYear: str
    joiningDate: str
    status: MemberStatus = MemberStatus.ACTIVE
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
