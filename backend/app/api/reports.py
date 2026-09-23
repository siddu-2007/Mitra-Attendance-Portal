"""Report Generation and File Export Endpoints (JSON, CSV, Excel, PDF)."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, Request
from app.core.config import settings
from app.core.firebase import get_db
from app.core.rate_limit import limiter
from app.core.security import get_current_admin
from app.schemas.reports import ExportFormat
from app.services.report_service import (
    build_daily_report,
    build_department_report,
    build_member_report,
    build_monthly_report,
    format_report_response,
)

router = APIRouter()


@router.get("/daily", summary="Generate Daily Attendance Report")
@limiter.limit(settings.RATE_LIMIT_REPORTS)
async def get_daily_report(
    request: Request,
    date: Optional[str] = Query(None, description="Report date (YYYY-MM-DD)"),
    departmentId: Optional[str] = Query(None, description="Optional department filter"),
    format: ExportFormat = Query(ExportFormat.JSON, description="Output format: json, csv, excel, pdf"),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Generate daily attendance report.
    Returns structured JSON for frontend tables or downloads binary CSV, Excel (.xlsx), or PDF.
    """
    headers, rows, summary, dict_rows = build_daily_report(
        db=db,
        date=date,
        department_id=departmentId,
        admin_id=current_admin.get("uid"),
        admin_name=current_admin.get("name"),
    )
    return format_report_response(
        report_title="Daily Attendance Report",
        headers=headers,
        rows=rows,
        summary=summary,
        dict_rows=dict_rows,
        export_format=format,
    )


@router.get("/monthly", summary="Generate Monthly Attendance Report")
@limiter.limit(settings.RATE_LIMIT_REPORTS)
async def get_monthly_report(
    request: Request,
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Year (e.g. 2026)"),
    departmentId: Optional[str] = Query(None, description="Optional department filter"),
    format: ExportFormat = Query(ExportFormat.JSON, description="Output format: json, csv, excel, pdf"),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Generate monthly attendance report showing member attendance percentages.
    Supports JSON, CSV, Excel, or PDF.
    """
    headers, rows, summary, dict_rows = build_monthly_report(
        db=db,
        month=month,
        year=year,
        department_id=departmentId,
        admin_id=current_admin.get("uid"),
        admin_name=current_admin.get("name"),
    )
    return format_report_response(
        report_title=f"Monthly Attendance Report {year}-{month:02d}",
        headers=headers,
        rows=rows,
        summary=summary,
        dict_rows=dict_rows,
        export_format=format,
    )


@router.get("/member", summary="Generate Individual Member Report")
@limiter.limit(settings.RATE_LIMIT_REPORTS)
async def get_member_report(
    request: Request,
    memberId: str = Query(..., description="Target member ID"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Optional month filter"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Optional year filter"),
    startDate: Optional[str] = Query(None, description="Optional start date"),
    endDate: Optional[str] = Query(None, description="Optional end date"),
    format: ExportFormat = Query(ExportFormat.JSON, description="Output format: json, csv, excel, pdf"),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Generate an individual member attendance report.
    Supports JSON, CSV, Excel, or PDF.
    """
    headers, rows, summary, dict_rows = build_member_report(
        db=db,
        member_id=memberId,
        month=month,
        year=year,
        start_date=startDate,
        end_date=endDate,
        admin_id=current_admin.get("uid"),
        admin_name=current_admin.get("name"),
    )
    return format_report_response(
        report_title=f"Member Attendance Dossier - {memberId}",
        headers=headers,
        rows=rows,
        summary=summary,
        dict_rows=dict_rows,
        export_format=format,
    )


@router.get("/department", summary="Generate Department Comparison Report")
@limiter.limit(settings.RATE_LIMIT_REPORTS)
async def get_department_report(
    request: Request,
    month: Optional[int] = Query(None, ge=1, le=12, description="Optional month filter"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Optional year filter"),
    format: ExportFormat = Query(ExportFormat.JSON, description="Output format: json, csv, excel, pdf"),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Generate department-level aggregated comparison report.
    Supports JSON, CSV, Excel, or PDF.
    """
    headers, rows, summary, dict_rows = build_department_report(
        db=db,
        month=month,
        year=year,
        admin_id=current_admin.get("uid"),
        admin_name=current_admin.get("name"),
    )
    return format_report_response(
        report_title="Department Attendance Comparison Report",
        headers=headers,
        rows=rows,
        summary=summary,
        dict_rows=dict_rows,
        export_format=format,
    )
