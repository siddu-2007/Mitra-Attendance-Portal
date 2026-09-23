"""Report generation service producing structured data and dispatching file exports."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from fastapi.responses import Response
from app.models.activity import ActivityAction
from app.schemas.reports import (
    DailyReportRow,
    DepartmentReportRow,
    ExportFormat,
    MemberReportRow,
    MonthlyReportRow,
    ReportDataResponse,
)
from app.services.activity_service import log_activity
from app.services.attendance_service import (
    get_member_attendance_history,
    get_monthly_attendance_summary,
    query_attendance_records,
)
from app.utils.calculations import calculate_attendance_percentage, summarize_attendance_statuses
from app.utils.exporters import export_to_csv, export_to_excel, export_to_pdf
from app.utils.validators import get_today_date_str, validate_iso_date, validate_month_year


def build_daily_report(
    db: Any,
    date: Optional[str] = None,
    department_id: Optional[str] = None,
    admin_id: Optional[str] = None,
    admin_name: Optional[str] = None,
) -> Tuple[List[str], List[List[Any]], Dict[str, Any], List[Dict[str, Any]]]:
    """Generate daily attendance tabular report."""
    target_date = validate_iso_date(date) if date else get_today_date_str()
    records = query_attendance_records(db=db, date=target_date, department_id=department_id)

    headers = ["Attendance ID", "Date", "Member ID", "Member Name", "Department", "Status", "Marked By"]
    rows: List[List[Any]] = []
    dict_rows: List[Dict[str, Any]] = []

    for r in records:
        row_obj = DailyReportRow(
            attendanceId=r.get("attendanceId", ""),
            date=r.get("date", ""),
            memberId=r.get("memberId", ""),
            memberName=r.get("memberName", ""),
            departmentName=r.get("departmentName", ""),
            status=r.get("status", ""),
            markedBy=r.get("markedBy", ""),
        )
        dict_rows.append(row_obj.model_dump())
        rows.append([
            row_obj.attendanceId,
            row_obj.date,
            row_obj.memberId,
            row_obj.memberName,
            row_obj.departmentName,
            row_obj.status,
            row_obj.markedBy,
        ])

    present, late, absent, total = summarize_attendance_statuses([r.get("status") for r in records])
    summary = {
        "date": target_date,
        "totalRecords": total,
        "present": present,
        "late": late,
        "absent": absent,
        "attendancePercentage": f"{calculate_attendance_percentage(present, late, total)}%",
    }

    if admin_id and admin_name:
        log_activity(
            db=db,
            admin_id=admin_id,
            admin_name=admin_name,
            action=ActivityAction.REPORT_GENERATED,
            target_type="REPORT_DAILY",
            target_id=target_date,
            metadata=summary,
        )

    return headers, rows, summary, dict_rows


def build_monthly_report(
    db: Any,
    month: int,
    year: int,
    department_id: Optional[str] = None,
    admin_id: Optional[str] = None,
    admin_name: Optional[str] = None,
) -> Tuple[List[str], List[List[Any]], Dict[str, Any], List[Dict[str, Any]]]:
    """Generate monthly attendance tabular report."""
    month, year = validate_month_year(month, year)
    data = get_monthly_attendance_summary(db=db, month=month, year=year, department_id=department_id)

    headers = [
        "Member ID",
        "Member Name",
        "Department",
        "Present Days",
        "Late Days",
        "Absent Days",
        "Total Sessions",
        "Attendance %",
    ]
    rows: List[List[Any]] = []
    dict_rows: List[Dict[str, Any]] = []

    for d in data:
        dict_rows.append(d.model_dump())
        rows.append([
            d.memberId,
            d.memberName,
            d.departmentName or "Unknown",
            d.presentDays,
            d.lateDays,
            d.absentDays,
            d.totalAttendanceDays,
            f"{d.attendancePercentage}%",
        ])

    total_sessions = sum(d.totalAttendanceDays for d in data)
    avg_pct = round(sum(d.attendancePercentage for d in data) / len(data), 2) if data else 0.0

    summary = {
        "month": f"{year:04d}-{month:02d}",
        "membersEvaluated": len(data),
        "totalRecordedSessions": total_sessions,
        "averageAttendance": f"{avg_pct}%",
    }

    if admin_id and admin_name:
        log_activity(
            db=db,
            admin_id=admin_id,
            admin_name=admin_name,
            action=ActivityAction.REPORT_GENERATED,
            target_type="REPORT_MONTHLY",
            target_id=f"{year:04d}-{month:02d}",
            metadata=summary,
        )

    return headers, rows, summary, dict_rows


def build_member_report(
    db: Any,
    member_id: str,
    month: Optional[int] = None,
    year: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_id: Optional[str] = None,
    admin_name: Optional[str] = None,
) -> Tuple[List[str], List[List[Any]], Dict[str, Any], List[Dict[str, Any]]]:
    """Generate comprehensive attendance dossier for an individual member."""
    history = get_member_attendance_history(
        db=db, member_id=member_id, month=month, year=year, start_date=start_date, end_date=end_date
    )

    headers = ["Date", "Department", "Status", "Marked By"]
    rows: List[List[Any]] = []
    dict_rows: List[Dict[str, Any]] = []

    for item in history.history:
        dict_rows.append(item.model_dump())
        rows.append([item.date, item.departmentName or "Unknown", item.status.value, item.markedBy])

    summary = {
        "memberId": history.memberId,
        "memberName": history.memberName,
        "department": history.departmentName,
        "overallPercentage": f"{history.overallAttendancePercentage}%",
        "totalSessions": history.totalSessions,
        "present": history.presentCount,
        "late": history.lateCount,
        "absent": history.absentCount,
    }

    if admin_id and admin_name:
        log_activity(
            db=db,
            admin_id=admin_id,
            admin_name=admin_name,
            action=ActivityAction.REPORT_GENERATED,
            target_type="REPORT_MEMBER",
            target_id=member_id,
            metadata=summary,
        )

    return headers, rows, summary, dict_rows


def build_department_report(
    db: Any,
    month: Optional[int] = None,
    year: Optional[int] = None,
    admin_id: Optional[str] = None,
    admin_name: Optional[str] = None,
) -> Tuple[List[str], List[List[Any]], Dict[str, Any], List[Dict[str, Any]]]:
    """Generate department-level aggregated comparison report."""
    dept_docs = db.collection("departments").stream()
    departments = [d.to_dict() for d in dept_docs]

    all_members = [m.to_dict() for m in db.collection("members").stream()]
    all_attendance = [a.to_dict() for a in db.collection("attendance").stream()]

    month_prefix = f"{year:04d}-{month:02d}" if month and year else None
    if month_prefix:
        all_attendance = [a for a in all_attendance if str(a.get("date", "")).startswith(month_prefix)]

    headers = [
        "Department Name",
        "Total Members",
        "Active Members",
        "Total Sessions Recorded",
        "Present Count",
        "Late Count",
        "Absent Count",
        "Overall Attendance %",
    ]
    rows: List[List[Any]] = []
    dict_rows: List[Dict[str, Any]] = []

    for dept in departments:
        d_id = dept.get("departmentId")
        d_name = dept.get("name", "Unknown")

        dept_members = [m for m in all_members if m.get("departmentId") == d_id]
        active_members = [m for m in dept_members if m.get("status") == "ACTIVE"]

        dept_attendance = [a for a in all_attendance if a.get("departmentId") == d_id]
        p, l, ab, tot = summarize_attendance_statuses([a.get("status") for a in dept_attendance])
        pct = calculate_attendance_percentage(p, l, tot)

        row_obj = DepartmentReportRow(
            departmentId=d_id,
            departmentName=d_name,
            totalMembers=len(dept_members),
            activeMembers=len(active_members),
            totalSessionsRecorded=tot,
            presentCount=p,
            lateCount=l,
            absentCount=ab,
            overallAttendancePercentage=pct,
        )
        dict_rows.append(row_obj.model_dump())
        rows.append([d_name, len(dept_members), len(active_members), tot, p, l, ab, f"{pct}%"])

    summary = {
        "departmentsCount": len(departments),
        "totalMembers": len(all_members),
        "period": month_prefix or "All Time",
    }

    if admin_id and admin_name:
        log_activity(
            db=db,
            admin_id=admin_id,
            admin_name=admin_name,
            action=ActivityAction.REPORT_GENERATED,
            target_type="REPORT_DEPARTMENT",
            target_id="ALL",
            metadata=summary,
        )

    return headers, rows, summary, dict_rows


def format_report_response(
    report_title: str,
    headers: List[str],
    rows: List[List[Any]],
    summary: Dict[str, Any],
    dict_rows: List[Dict[str, Any]],
    export_format: ExportFormat,
) -> Any:
    """Return JSON or binary file response based on the requested format."""
    clean_filename = f"mithra_{report_title.lower().replace(' ', '_')}"

    if export_format == ExportFormat.CSV:
        csv_bytes = export_to_csv(headers, rows)
        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{clean_filename}.csv"'},
        )
    elif export_format == ExportFormat.EXCEL:
        excel_bytes = export_to_excel(report_title, headers, rows)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{clean_filename}.xlsx"'},
        )
    elif export_format == ExportFormat.PDF:
        pdf_bytes = export_to_pdf(report_title, headers, rows, summary=summary)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{clean_filename}.pdf"'},
        )

    # Default: JSON envelope
    return {
        "success": True,
        "message": f"{report_title} generated successfully.",
        "data": {
            "reportType": report_title,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "headers": headers,
            "rows": dict_rows,
        },
    }
