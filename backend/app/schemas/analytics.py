"""Schemas for Analytics aggregations and trend reporting."""

from typing import Dict, List, Optional
from pydantic import BaseModel


class AttendanceDistribution(BaseModel):
    present: int
    absent: int
    late: int


class MonthlyTrendItem(BaseModel):
    month: str  # e.g., "2026-08"
    monthLabel: str  # e.g., "Aug 2026"
    attendancePercentage: float
    totalRecords: int


class DepartmentAnalyticsStat(BaseModel):
    departmentId: str
    departmentName: str
    totalRecords: int
    presentCount: int
    attendancePercentage: float


class AnalyticsResponse(BaseModel):
    overallAttendance: float
    monthlyTrend: List[MonthlyTrendItem]
    departmentStatistics: List[DepartmentAnalyticsStat]
    attendanceDistribution: AttendanceDistribution
