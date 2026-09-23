"""Analytics aggregation service for trends, distribution, and department comparisons."""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.schemas.analytics import (
    AnalyticsResponse,
    AttendanceDistribution,
    DepartmentAnalyticsStat,
    MonthlyTrendItem,
)
from app.utils.calculations import calculate_attendance_percentage, summarize_attendance_statuses


def get_analytics_data(
    db: Any,
    department_id: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> AnalyticsResponse:
    """Compute overall attendance, monthly trends, department statistics, and distribution."""
    # Pre-fetch department lookup
    dept_docs = db.collection("departments").stream()
    dept_map = {d.to_dict().get("departmentId"): d.to_dict().get("name") for d in dept_docs}

    # Fetch attendance records
    attendance_docs = db.collection("attendance").stream()
    all_attendance = [a.to_dict() for a in attendance_docs]

    # Filter attendance records
    filtered = []
    month_prefix = f"{year:04d}-{month:02d}" if month and year else None

    for r in all_attendance:
        r_date = r.get("date", "")
        if department_id and r.get("departmentId") != department_id:
            continue
        if month_prefix and not r_date.startswith(month_prefix):
            continue
        if start_date and r_date < start_date:
            continue
        if end_date and r_date > end_date:
            continue
        filtered.append(r)

    # 1. Distribution and overall attendance
    present, late, absent, total = summarize_attendance_statuses([r.get("status") for r in filtered])
    overall_pct = calculate_attendance_percentage(present, late, total)
    distribution = AttendanceDistribution(present=present, absent=absent, late=late)

    # 2. Monthly Trend aggregation
    trend_dict = defaultdict(list)
    for r in filtered:
        d_str = r.get("date", "")
        if len(d_str) >= 7:
            m_key = d_str[:7]  # YYYY-MM
            trend_dict[m_key].append(r.get("status"))

    monthly_trend: List[MonthlyTrendItem] = []
    for m_key in sorted(trend_dict.keys()):
        m_statuses = trend_dict[m_key]
        m_present, m_late, m_absent, m_total = summarize_attendance_statuses(m_statuses)
        pct = calculate_attendance_percentage(m_present, m_late, m_total)

        # Format label e.g., "Aug 2026"
        try:
            dt = datetime.strptime(m_key, "%Y-%m")
            label = dt.strftime("%b %Y")
        except ValueError:
            label = m_key

        monthly_trend.append(
            MonthlyTrendItem(
                month=m_key,
                monthLabel=label,
                attendancePercentage=pct,
                totalRecords=m_total,
            )
        )

    # 3. Department Statistics aggregation
    dept_records = defaultdict(list)
    for r in filtered:
        d_id = r.get("departmentId", "GENERAL")
        dept_records[d_id].append(r.get("status"))

    department_statistics: List[DepartmentAnalyticsStat] = []
    for d_id, statuses in dept_records.items():
        d_present, d_late, d_absent, d_total = summarize_attendance_statuses(statuses)
        d_pct = calculate_attendance_percentage(d_present, d_late, d_total)
        d_name = dept_map.get(d_id, "Unknown Department")

        department_statistics.append(
            DepartmentAnalyticsStat(
                departmentId=d_id,
                departmentName=d_name,
                totalRecords=d_total,
                presentCount=d_present + d_late,
                attendancePercentage=d_pct,
            )
        )

    department_statistics.sort(key=lambda x: x.departmentName.lower())

    return AnalyticsResponse(
        overallAttendance=overall_pct,
        monthlyTrend=monthly_trend,
        departmentStatistics=department_statistics,
        attendanceDistribution=distribution,
    )
