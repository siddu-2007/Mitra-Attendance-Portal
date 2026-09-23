"""Schemas for the unified Dashboard API endpoint."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.models.activity import ActivityLogModel


class DepartmentDashboardStat(BaseModel):
    departmentId: str
    departmentName: str
    totalMembers: int
    presentToday: int
    attendancePercentage: float


class DashboardResponse(BaseModel):
    totalActiveMembers: int
    todayPresent: int
    todayAbsent: int
    todayLate: int
    todayAttendancePercentage: float
    monthlyAttendancePercentage: float
    departmentStatistics: List[DepartmentDashboardStat]
    recentActivity: List[Dict[str, Any]]
