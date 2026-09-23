"""Department Management Service."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from app.core.logging import logger
from app.models.activity import ActivityAction
from app.models.department import DepartmentModel, DepartmentStatus
from app.schemas.department import DepartmentCreate, DepartmentStatusUpdate, DepartmentUpdate
from app.services.activity_service import log_activity


def list_departments(db: Any, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all departments, optionally filtered by status (ACTIVE/INACTIVE)."""
    query = db.collection("departments")
    if status_filter:
        query = query.where("status", "==", status_filter.upper())

    docs = query.stream()
    depts = [d.to_dict() for d in docs]
    depts.sort(key=lambda x: x.get("name", "").lower())
    return depts


def get_department_by_id(db: Any, department_id: str) -> Dict[str, Any]:
    """Retrieve a department by its ID or raise 404."""
    doc = db.collection("departments").document(department_id).get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": f"Department '{department_id}' not found.",
                "error": "DEPARTMENT_NOT_FOUND",
            },
        )
    return doc.to_dict()


def create_department(
    db: Any,
    dept_in: DepartmentCreate,
    admin_id: str,
    admin_name: str,
) -> Dict[str, Any]:
    """Create a new department, ensuring no duplicate active name exists."""
    name_clean = dept_in.name.strip()
    if not name_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False, "message": "Department name cannot be empty.", "error": "VALIDATION_ERROR"},
        )

    # Check for duplicate active department name
    existing_docs = db.collection("departments").where("status", "==", DepartmentStatus.ACTIVE.value).stream()
    for d in existing_docs:
        data = d.to_dict()
        if data.get("name", "").strip().lower() == name_clean.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": f"An active department named '{name_clean}' already exists.",
                    "error": "DUPLICATE_DEPARTMENT",
                },
            )

    dept_id = f"DEPT_{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc).isoformat()

    dept_data = DepartmentModel(
        departmentId=dept_id,
        name=name_clean,
        status=DepartmentStatus.ACTIVE,
        createdAt=now,
        updatedAt=now,
    ).model_dump()

    db.collection("departments").document(dept_id).set(dept_data)

    log_activity(
        db=db,
        admin_id=admin_id,
        admin_name=admin_name,
        action=ActivityAction.DEPARTMENT_CREATED,
        target_type="DEPARTMENT",
        target_id=dept_id,
        metadata={"name": name_clean},
    )

    return dept_data


def update_department(
    db: Any,
    department_id: str,
    dept_in: DepartmentUpdate,
    admin_id: str,
    admin_name: str,
) -> Dict[str, Any]:
    """Update department details."""
    dept = get_department_by_id(db, department_id)

    updates: Dict[str, Any] = {}
    if dept_in.name is not None:
        name_clean = dept_in.name.strip()
        if not name_clean:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"success": False, "message": "Department name cannot be blank.", "error": "VALIDATION_ERROR"},
            )

        # Check duplicate name among other active departments
        existing_docs = db.collection("departments").where("status", "==", DepartmentStatus.ACTIVE.value).stream()
        for d in existing_docs:
            data = d.to_dict()
            if data.get("departmentId") != department_id and data.get("name", "").strip().lower() == name_clean.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "success": False,
                        "message": f"Another active department named '{name_clean}' already exists.",
                        "error": "DUPLICATE_DEPARTMENT",
                    },
                )
        updates["name"] = name_clean

    if not updates:
        return dept

    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()
    db.collection("departments").document(department_id).update(updates)

    log_activity(
        db=db,
        admin_id=admin_id,
        admin_name=admin_name,
        action=ActivityAction.DEPARTMENT_UPDATED,
        target_type="DEPARTMENT",
        target_id=department_id,
        metadata=updates,
    )

    updated_dept = db.collection("departments").document(department_id).get()
    return updated_dept.to_dict()


def set_department_status(
    db: Any,
    department_id: str,
    status_update: DepartmentStatusUpdate,
    admin_id: str,
    admin_name: str,
) -> Dict[str, Any]:
    """Activate or deactivate department. Prevents hard deletion."""
    dept = get_department_by_id(db, department_id)

    # If deactivating, verify if any active members exist
    if status_update.status == DepartmentStatus.INACTIVE:
        active_members = (
            db.collection("members")
            .where("departmentId", "==", department_id)
            .where("status", "==", "ACTIVE")
            .stream()
        )
        active_list = list(active_members)
        if len(active_list) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": f"Cannot deactivate department. {len(active_list)} active member(s) are assigned to it. Reassign or deactivate them first.",
                    "error": "DEPARTMENT_IN_USE",
                },
            )

    now = datetime.now(timezone.utc).isoformat()
    db.collection("departments").document(department_id).update({
        "status": status_update.status.value,
        "updatedAt": now,
    })

    log_activity(
        db=db,
        admin_id=admin_id,
        admin_name=admin_name,
        action=ActivityAction.DEPARTMENT_UPDATED,
        target_type="DEPARTMENT",
        target_id=department_id,
        metadata={"new_status": status_update.status.value},
    )

    updated_dept = db.collection("departments").document(department_id).get()
    return updated_dept.to_dict()
