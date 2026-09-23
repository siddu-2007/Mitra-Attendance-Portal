"""Optimized Single-Request Dashboard Service."""

from datetime import datetime, timezone
from typing import Any, Dict, List
from app.schemas.dashboard import DashboardResponse, DepartmentDashboardStat
from app.services.activity_service import query_activity_logs
from app.utils.calculations import calculate_attendance_percentage, summarize_attendance_statuses
from app.utils.validators import get_today_date_str


def get_dashboard_metrics(db: Any) -> DashboardResponse:
    """
    Produce all top-level KPIs, today's breakdown, monthly percentage,
    department statistics, and recent activity logs in one consolidated call.
    """
    today_str = get_today_date_str()
    now_utc = datetime.now(timezone.utc)
    current_month_prefix = now_utc.strftime("%Y-%m")

    # 1. Active members and department mapping
    members_docs = db.collection("members").stream()
    all_members = [m.to_dict() for m in members_docs]
    active_members = [m for m in all_members if m.get("status") == "ACTIVE"]
    total_active_members = len(active_members)

    # 2. Departments lookup
    dept_docs = db.collection("departments").stream()
    dept_map: Dict[str, str] = {d.to_dict().get("departmentId"): d.to_dict().get("name") for d in dept_docs}

    # Department active member count
    dept_member_counts: Dict[str, int] = {}
    for m in active_members:
        dept_id = m.get("departmentId", "GENERAL")
        dept_member_counts[dept_id] = dept_member_counts.get(dept_id, 0) + 1

    # 3. Attendance records
    attendance_docs = db.collection("attendance").stream()
    all_attendance = [a.to_dict() for a in attendance_docs]

    # Filter today's records
    today_records = [a for a in all_attendance if a.get("date") == today_str]
    today_present, today_late, today_absent, today_total = summarize_attendance_statuses(
        [a.get("status") for a in today_records]
    )

    # If today's total is recorded against total active members, or recorded sessions:
    # Use standard calculation: ((present + late) / total_recorded) * 100
    today_percentage = calculate_attendance_percentage(today_present, today_late, today_total)

    # 4. Monthly records
    month_records = [a for a in all_attendance if str(a.get("date", "")).startswith(current_month_prefix)]
    m_present, m_late, m_absent, m_total = summarize_attendance_statuses([a.get("status") for a in month_records])
    monthly_percentage = calculate_attendance_percentage(m_present, m_late, m_total)

    # 5. Department statistics for today
    today_present_by_dept: Dict[str, int] = {}
    for a in today_records:
        if a.get("status") in ("PRESENT", "LATE"):
            dept_id = a.get("departmentId", "GENERAL")
            today_present_by_dept[dept_id] = today_present_by_dept.get(dept_id, 0) + 1

    dept_stats: List[DepartmentDashboardStat] = []
    for dept_id, dept_name in dept_map.items():
        m_count = dept_member_counts.get(dept_id, 0)
        present_count = today_present_by_dept.get(dept_id, 0)
        dept_pct = calculate_attendance_percentage(present_count, 0, m_count) if m_count > 0 else 0.0

        dept_stats.append(
            DepartmentDashboardStat(
                departmentId=dept_id,
                departmentName=dept_name,
                totalMembers=m_count,
                presentToday=present_count,
                attendancePercentage=dept_pct,
            )
        )

    dept_stats.sort(key=lambda x: x.departmentName.lower())

    # 6. Recent activity (top 5)
    recent_logs = query_activity_logs(db=db, limit=5)

    return DashboardResponse(
        totalActiveMembers=total_active_members,
        todayPresent=today_present,
        todayAbsent=today_absent,
        todayLate=today_late,
        todayAttendancePercentage=today_percentage,
        monthlyAttendancePercentage=monthly_percentage,
        departmentStatistics=dept_stats,
        recentActivity=recent_logs,
    )
