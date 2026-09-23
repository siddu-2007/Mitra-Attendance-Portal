"""Schemas for tabular reports and export configurations."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"


class DailyReportRow(BaseModel):
    attendanceId: str
    date: str
    memberId: str
    memberName: str
    departmentName: str
    status: str
    markedBy: str


class MonthlyReportRow(BaseModel):
    memberId: str
    memberName: str
    departmentName: str
    academicYear: str
    presentDays: int
    lateDays: int
    absentDays: int
    totalSessions: int
    attendancePercentage: float


class MemberReportRow(BaseModel):
    date: str
    departmentName: str
    status: str
    markedBy: str


class DepartmentReportRow(BaseModel):
    departmentId: str
    departmentName: str
    totalMembers: int
    activeMembers: int
    totalSessionsRecorded: int
    presentCount: int
    lateCount: int
    absentCount: int
    overallAttendancePercentage: float


class ReportDataResponse(BaseModel):
    reportType: str
    generatedAt: str
    filtersApplied: Dict[str, Any]
    summary: Dict[str, Any]
    rows: List[Dict[str, Any]]
