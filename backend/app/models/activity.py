"""Activity log collection entity models and action enums."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ActivityAction(str, Enum):
    ADMIN_LOGIN = "ADMIN_LOGIN"
    MEMBER_CREATED = "MEMBER_CREATED"
    MEMBER_UPDATED = "MEMBER_UPDATED"
    MEMBER_DEACTIVATED = "MEMBER_DEACTIVATED"
    ATTENDANCE_CREATED = "ATTENDANCE_CREATED"
    ATTENDANCE_UPDATED = "ATTENDANCE_UPDATED"
    DEPARTMENT_CREATED = "DEPARTMENT_CREATED"
    DEPARTMENT_UPDATED = "DEPARTMENT_UPDATED"
    REPORT_GENERATED = "REPORT_GENERATED"


class ActivityLogModel(BaseModel):
    logId: str
    adminId: str
    adminName: str
    action: ActivityAction
    targetType: Optional[str] = None
    targetId: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
