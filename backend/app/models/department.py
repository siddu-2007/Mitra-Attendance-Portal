"""Department collection entity models and enums."""

from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class DepartmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class DepartmentModel(BaseModel):
    departmentId: str
    name: str
    status: DepartmentStatus = DepartmentStatus.ACTIVE
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
