"""Attendance Recording, Bulk Processing, and Summary Endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from app.core.config import settings
from app.core.firebase import get_db
from app.core.rate_limit import limiter
from app.core.security import get_current_admin, require_president
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    BulkAttendanceRequest,
    BulkAttendanceResponse,
    MarkAllPresentRequest,
    MonthlyAttendanceRow,
)
from app.schemas.common import APIResponse
from app.services.attendance_service import (
    create_attendance_record,
    delete_attendance_record,
    get_attendance_by_id,
    get_monthly_attendance_summary,
    mark_all_active_present,
    process_bulk_attendance,
    query_attendance_records,
    update_attendance_record,
)

router = APIRouter()


@router.post("", response_model=APIResponse[AttendanceResponse], status_code=status.HTTP_201_CREATED, summary="Create Attendance")
async def record_attendance(
    attendance_in: AttendanceCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Create a single daily attendance record.
    Prevents duplicate attendance for memberId + date (returns HTTP 409).
    """
    record = create_attendance_record(
        db=db,
        attendance_in=attendance_in,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
    )
    return APIResponse(
        success=True,
        message="Attendance recorded successfully.",
        data=AttendanceResponse(**record),
    )


@router.get("", response_model=APIResponse[List[AttendanceResponse]], summary="Query Attendance Records")
async def get_attendance_list(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD"),
    departmentId: Optional[str] = Query(None, description="Filter by department"),
    memberId: Optional[str] = Query(None, description="Filter by member ID"),
    status: Optional[str] = Query(None, description="Filter by status: PRESENT, ABSENT, LATE"),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Query attendance records filtered by date, department, member, and status."""
    records = query_attendance_records(
        db=db,
        date=date,
        department_id=departmentId,
        member_id=memberId,
        status_filter=status,
        limit=limit,
    )
    return APIResponse(
        success=True,
        message=f"Retrieved {len(records)} attendance record(s).",
        data=[AttendanceResponse(**r) for r in records],
    )


@router.post("/bulk", response_model=APIResponse[BulkAttendanceResponse], summary="Submit Bulk Attendance")
@limiter.limit(settings.RATE_LIMIT_BULK)
async def submit_bulk_attendance(
    request: Request,
    bulk_request: BulkAttendanceRequest,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Submit attendance for multiple members simultaneously.
    Validates each record, skips duplicates, and returns clear success/duplicate/failed breakdowns.
    """
    result = process_bulk_attendance(
        db=db,
        bulk_request=bulk_request,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
    )
    return APIResponse(
        success=True,
        message="Bulk attendance processed.",
        data=result,
    )


@router.post("/mark-all-present", response_model=APIResponse[BulkAttendanceResponse], summary="Mark All Present")
async def mark_all_present(
    req: MarkAllPresentRequest,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Bulk marks all active members (or members of a selected department) as PRESENT.
    Enforces business rules and prevents duplicate records.
    """
    result = mark_all_active_present(
        db=db,
        date_str=req.date,
        department_id=req.departmentId,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
    )
    return APIResponse(
        success=True,
        message=f"Marked {result.summary.successful} active member(s) present.",
        data=result,
    )


@router.get("/monthly", response_model=APIResponse[List[MonthlyAttendanceRow]], summary="Get Monthly Attendance Summary")
async def get_monthly_attendance(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Year (e.g. 2026)"),
    departmentId: Optional[str] = Query(None, description="Optional department filter"),
    memberId: Optional[str] = Query(None, description="Optional member ID filter"),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Aggregates attendance by member for a specific month and year.
    Calculates: Attendance Percentage = ((Present + Late) / Total Sessions) * 100
    """
    rows = get_monthly_attendance_summary(
        db=db,
        month=month,
        year=year,
        department_id=departmentId,
        member_id=memberId,
    )
    return APIResponse(
        success=True,
        message=f"Monthly attendance summary calculated for {year:04d}-{month:02d}.",
        data=rows,
    )


@router.get("/{attendance_id}", response_model=APIResponse[AttendanceResponse], summary="Get Attendance Record")
async def get_single_attendance(
    attendance_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Retrieve details of an attendance record."""
    record = get_attendance_by_id(db=db, attendance_id=attendance_id)
    return APIResponse(
        success=True,
        message="Attendance record found.",
        data=AttendanceResponse(**record),
    )


@router.put("/{attendance_id}", response_model=APIResponse[AttendanceResponse], summary="Update Attendance Record")
async def modify_attendance(
    attendance_id: str,
    attendance_in: AttendanceUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Modify an existing attendance status. Records an activity audit log."""
    updated = update_attendance_record(
        db=db,
        attendance_id=attendance_id,
        attendance_in=attendance_in,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
    )
    return APIResponse(
        success=True,
        message="Attendance record updated.",
        data=AttendanceResponse(**updated),
    )


@router.delete("/{attendance_id}", response_model=APIResponse[Dict[str, str]], summary="Delete Attendance Record")
async def remove_attendance(
    attendance_id: str,
    current_admin: Dict[str, Any] = Depends(require_president),
    db: Any = Depends(get_db),
):
    """Delete an attendance record. Restricted to President."""
    delete_attendance_record(
        db=db,
        attendance_id=attendance_id,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
    )
    return APIResponse(
        success=True,
        message=f"Attendance record '{attendance_id}' has been removed.",
        data={"attendanceId": attendance_id},
    )
