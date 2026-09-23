"""Member Management Endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.firebase import get_db
from app.core.security import get_current_admin
from app.schemas.attendance import MemberAttendanceHistoryResponse
from app.schemas.common import APIResponse
from app.schemas.member import (
    MemberCreate,
    MemberResponse,
    MemberStatusUpdate,
    MemberUpdate,
)
from app.services.attendance_service import get_member_attendance_history
from app.services.member_service import (
    create_member,
    get_member_by_id,
    list_members,
    set_member_status,
    update_member,
)

router = APIRouter()


@router.get("", response_model=APIResponse[List[MemberResponse]], summary="List Members")
async def get_all_members(
    search: Optional[str] = Query(None, description="Search term for name, memberId, or email"),
    department: Optional[str] = Query(None, description="Filter by departmentId"),
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE or INACTIVE"),
    academicYear: Optional[str] = Query(None, description="Filter by academic year"),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """List members supporting text search, department, status, and academicYear filtering."""
    members = list_members(
        db=db,
        search=search,
        department_id=department,
        status_filter=status,
        academic_year=academicYear,
    )
    return APIResponse(
        success=True,
        message=f"Retrieved {len(members)} member(s).",
        data=[MemberResponse(**m) for m in members],
    )


@router.post("", response_model=APIResponse[MemberResponse], status_code=status.HTTP_201_CREATED, summary="Create Member")
async def create_new_member(
    member_in: MemberCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Register a new member. Validates unique member ID and department existence."""
    created = create_member(
        db=db,
        member_in=member_in,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
    )
    return APIResponse(
        success=True,
        message=f"Member '{created['name']}' registered successfully.",
        data=MemberResponse(**created),
    )


@router.get("/{member_id}", response_model=APIResponse[MemberResponse], summary="Get Member by ID")
async def get_single_member(
    member_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Retrieve full profile of a single member."""
    member = get_member_by_id(db=db, member_id=member_id)
    return APIResponse(
        success=True,
        message="Member profile found.",
        data=MemberResponse(**member),
    )


@router.put("/{member_id}", response_model=APIResponse[MemberResponse], summary="Update Member")
async def update_existing_member(
    member_id: str,
    member_in: MemberUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Update member details."""
    updated = update_member(
        db=db,
        member_id=member_id,
        member_in=member_in,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
    )
    return APIResponse(
        success=True,
        message="Member profile updated.",
        data=MemberResponse(**updated),
    )


@router.patch("/{member_id}/status", response_model=APIResponse[MemberResponse], summary="Toggle Member Status")
async def update_status_of_member(
    member_id: str,
    status_in: MemberStatusUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Soft activate or deactivate a member. Historical attendance is strictly preserved."""
    updated = set_member_status(
        db=db,
        member_id=member_id,
        status_update=status_in,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
    )
    return APIResponse(
        success=True,
        message=f"Member status changed to {status_in.status.value}.",
        data=MemberResponse(**updated),
    )


@router.get("/{member_id}/attendance", response_model=APIResponse[MemberAttendanceHistoryResponse], summary="Get Member Attendance")
async def get_attendance_for_member(
    member_id: str,
    month: Optional[int] = Query(None, ge=1, le=12, description="Month (1-12)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Year (e.g. 2026)"),
    startDate: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    endDate: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Retrieve detailed attendance history and overall attendance percentage for a member."""
    history = get_member_attendance_history(
        db=db,
        member_id=member_id,
        month=month,
        year=year,
        start_date=startDate,
        end_date=endDate,
    )
    return APIResponse(
        success=True,
        message=f"Attendance history retrieved for member {member_id}.",
        data=history,
    )
