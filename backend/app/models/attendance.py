"""Attendance collection entity models and enums."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"


class AttendanceRecordModel(BaseModel):
    attendanceId: str
    memberId: str
    date: str  # YYYY-MM-DD
    status: AttendanceStatus
    departmentId: str
    markedBy: str
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @staticmethod
    def generate_id(member_id: str, date_str: str) -> str:
        """Create deterministic attendance ID to prevent duplication."""
        return f"{member_id.strip()}_{date_str.strip()}"
