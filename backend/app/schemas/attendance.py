"""Schemas for Attendance recording, bulk submissions, and calculations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.attendance import AttendanceStatus


class AttendanceCreate(BaseModel):
    memberId: str = Field(..., description="Target member ID, e.g. 24PA1A4511")
    date: str = Field(..., description="Attendance date in YYYY-MM-DD format")
    status: AttendanceStatus = Field(..., description="PRESENT, ABSENT, or LATE")
    departmentId: Optional[str] = Field(None, description="Optional department ID (auto-resolved if omitted)")


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus = Field(..., description="Updated status: PRESENT, ABSENT, or LATE")


class AttendanceResponse(BaseModel):
    attendanceId: str
    memberId: str
    memberName: Optional[str] = None
    date: str
    status: AttendanceStatus
    departmentId: str
    departmentName: Optional[str] = None
    markedBy: str
    createdAt: str
    updatedAt: str


class BulkAttendanceRecord(BaseModel):
    memberId: str = Field(..., description="Member ID")
    status: AttendanceStatus = Field(default=AttendanceStatus.PRESENT)


class BulkAttendanceRequest(BaseModel):
    date: str = Field(..., description="Attendance date YYYY-MM-DD")
    records: List[BulkAttendanceRecord] = Field(..., min_length=1, description="List of member attendance records")


class BulkAttendanceSummary(BaseModel):
    total: int
    successful: int
    duplicates: int
    failed: int


class BulkAttendanceResponse(BaseModel):
    summary: BulkAttendanceSummary
    successful: List[str]
    duplicates: List[str]
    failed: List[Dict[str, str]]


class MarkAllPresentRequest(BaseModel):
    date: str = Field(..., description="Attendance date YYYY-MM-DD")
    departmentId: Optional[str] = Field(None, description="Optional department filter")


class MonthlyAttendanceRow(BaseModel):
    memberId: str
    memberName: str
    departmentId: str
    departmentName: Optional[str] = None
    presentDays: int
    absentDays: int
    lateDays: int
    totalAttendanceDays: int
    attendancePercentage: float


class MemberAttendanceHistoryResponse(BaseModel):
    memberId: str
    memberName: str
    departmentId: str
    departmentName: Optional[str] = None
    overallAttendancePercentage: float
    totalSessions: int
    presentCount: int
    absentCount: int
    lateCount: int
    history: List[AttendanceResponse]
