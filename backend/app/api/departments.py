"""Department Endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.firebase import get_db
from app.core.security import get_current_admin
from app.schemas.common import APIResponse
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentStatusUpdate,
    DepartmentUpdate,
)
from app.services.department_service import (
    create_department,
    get_department_by_id,
    list_departments,
    set_department_status,
    update_department,
)

router = APIRouter()


@router.get("", response_model=APIResponse[List[DepartmentResponse]], summary="List Departments")
async def get_all_departments(
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE or INACTIVE"),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Retrieve all departments with optional status filtering."""
    depts = list_departments(db=db, status_filter=status)
    return APIResponse(
        success=True,
        message="Departments retrieved successfully.",
        data=[DepartmentResponse(**d) for d in depts],
    )


@router.post("", response_model=APIResponse[DepartmentResponse], status_code=status.HTTP_201_CREATED, summary="Create Department")
async def create_new_department(
    dept_in: DepartmentCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Create a new department. Prevents duplicate active department names."""
    created = create_department(
        db=db,
        dept_in=dept_in,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
    )
    return APIResponse(
        success=True,
        message=f"Department '{dept_in.name}' created successfully.",
        data=DepartmentResponse(**created),
    )


@router.get("/{department_id}", response_model=APIResponse[DepartmentResponse], summary="Get Department by ID")
async def get_single_department(
    department_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Retrieve details of a specific department."""
    dept = get_department_by_id(db=db, department_id=department_id)
    return APIResponse(
        success=True,
        message="Department found.",
        data=DepartmentResponse(**dept),
    )


@router.put("/{department_id}", response_model=APIResponse[DepartmentResponse], summary="Update Department")
async def update_existing_department(
    department_id: str,
    dept_in: DepartmentUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """Update department properties."""
    updated = update_department(
        db=db,
        department_id=department_id,
        dept_in=dept_in,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
    )
    return APIResponse(
        success=True,
        message="Department updated successfully.",
        data=DepartmentResponse(**updated),
    )


@router.patch("/{department_id}/status", response_model=APIResponse[DepartmentResponse], summary="Update Department Status")
async def update_status_of_department(
    department_id: str,
    status_in: DepartmentStatusUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Toggle department active/inactive status.
    Guards against deactivating departments with active assigned members.
    """
    updated = set_department_status(
        db=db,
        department_id=department_id,
        status_update=status_in,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
    )
    return APIResponse(
        success=True,
        message=f"Department status changed to {status_in.status.value}.",
        data=DepartmentResponse(**updated),
    )
