"""Member Management Service."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from app.core.logging import logger
from app.models.activity import ActivityAction
from app.models.member import MemberModel, MemberStatus
from app.schemas.member import MemberCreate, MemberStatusUpdate, MemberUpdate
from app.services.activity_service import log_activity
from app.utils.validators import sanitize_member_id, validate_iso_date


def get_member_by_id(db: Any, member_id: str) -> Dict[str, Any]:
    """Retrieve member by unique memberId or raise 404."""
    clean_id = sanitize_member_id(member_id)
    doc = db.collection("members").document(clean_id).get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": f"Member with ID '{clean_id}' was not found.",
                "error": "MEMBER_NOT_FOUND",
            },
        )
    data = doc.to_dict()

    # Enrich with department name
    dept_id = data.get("departmentId")
    if dept_id:
        dept_doc = db.collection("departments").document(dept_id).get()
        if dept_doc.exists:
            data["departmentName"] = dept_doc.to_dict().get("name", "Unknown")

    return data


def create_member(
    db: Any,
    member_in: MemberCreate,
    admin_id: str,
    admin_name: str,
) -> Dict[str, Any]:
    """Create a new member with uniqueness check and department validation."""
    clean_id = sanitize_member_id(member_in.memberId)

    # Check for uniqueness
    existing_doc = db.collection("members").document(clean_id).get()
    if existing_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": f"Member ID '{clean_id}' is already registered.",
                "error": "DUPLICATE_MEMBER_ID",
            },
        )

    # Validate department exists
    dept_doc = db.collection("departments").document(member_in.departmentId).get()
    if not dept_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": f"Department with ID '{member_in.departmentId}' does not exist.",
                "error": "INVALID_DEPARTMENT",
            },
        )
    dept_name = dept_doc.to_dict().get("name")

    # Validate joiningDate format
    joining_date = validate_iso_date(member_in.joiningDate)

    now = datetime.now(timezone.utc).isoformat()
    member_data = MemberModel(
        memberId=clean_id,
        name=member_in.name.strip(),
        email=str(member_in.email).strip().lower(),
        phone=member_in.phone.strip() if member_in.phone else None,
        departmentId=member_in.departmentId,
        academicYear=member_in.academicYear.strip(),
        joiningDate=joining_date,
        status=MemberStatus.ACTIVE,
        createdAt=now,
        updatedAt=now,
    ).model_dump()

    db.collection("members").document(clean_id).set(member_data)

    log_activity(
        db=db,
        admin_id=admin_id,
        admin_name=admin_name,
        action=ActivityAction.MEMBER_CREATED,
        target_type="MEMBER",
        target_id=clean_id,
        metadata={"name": member_in.name, "departmentId": member_in.departmentId},
    )

    member_data["departmentName"] = dept_name
    return member_data


def list_members(
    db: Any,
    search: Optional[str] = None,
    department_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    academic_year: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List members supporting search, department, status, and academicYear filters."""
    query = db.collection("members")

    if status_filter:
        query = query.where("status", "==", status_filter.upper())
    if department_id:
        query = query.where("departmentId", "==", department_id)
    if academic_year:
        query = query.where("academicYear", "==", academic_year)

    docs = query.stream()
    members = [d.to_dict() for d in docs]

    # Pre-fetch department lookup table
    dept_docs = db.collection("departments").stream()
    dept_lookup = {d.to_dict().get("departmentId"): d.to_dict().get("name") for d in dept_docs}

    # Text search filter (matches name, memberId, email)
    if search:
        s = search.strip().lower()
        members = [
            m
            for m in members
            if s in m.get("name", "").lower()
            or s in m.get("memberId", "").lower()
            or s in m.get("email", "").lower()
        ]

    for m in members:
        m["departmentName"] = dept_lookup.get(m.get("departmentId"), "Unknown")

    members.sort(key=lambda x: x.get("name", "").lower())
    return members


def update_member(
    db: Any,
    member_id: str,
    member_in: MemberUpdate,
    admin_id: str,
    admin_name: str,
) -> Dict[str, Any]:
    """Update member profile details."""
    clean_id = sanitize_member_id(member_id)
    current = get_member_by_id(db, clean_id)

    updates: Dict[str, Any] = {}
    if member_in.name is not None:
        updates["name"] = member_in.name.strip()
    if member_in.email is not None:
        updates["email"] = str(member_in.email).strip().lower()
    if member_in.phone is not None:
        updates["phone"] = member_in.phone.strip()
    if member_in.academicYear is not None:
        updates["academicYear"] = member_in.academicYear.strip()
    if member_in.joiningDate is not None:
        updates["joiningDate"] = validate_iso_date(member_in.joiningDate)
    if member_in.departmentId is not None:
        dept_doc = db.collection("departments").document(member_in.departmentId).get()
        if not dept_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "message": "Specified department does not exist.", "error": "INVALID_DEPARTMENT"},
            )
        updates["departmentId"] = member_in.departmentId

    if not updates:
        return current

    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()
    db.collection("members").document(clean_id).update(updates)

    log_activity(
        db=db,
        admin_id=admin_id,
        admin_name=admin_name,
        action=ActivityAction.MEMBER_UPDATED,
        target_type="MEMBER",
        target_id=clean_id,
        metadata=updates,
    )

    return get_member_by_id(db, clean_id)


def set_member_status(
    db: Any,
    member_id: str,
    status_update: MemberStatusUpdate,
    admin_id: str,
    admin_name: str,
) -> Dict[str, Any]:
    """Soft deactivation/activation of member. Preserves all historical attendance."""
    clean_id = sanitize_member_id(member_id)
    get_member_by_id(db, clean_id)  # Throws 404 if not found

    now = datetime.now(timezone.utc).isoformat()
    db.collection("members").document(clean_id).update({
        "status": status_update.status.value,
        "updatedAt": now,
    })

    action = (
        ActivityAction.MEMBER_DEACTIVATED
        if status_update.status == MemberStatus.INACTIVE
        else ActivityAction.MEMBER_UPDATED
    )

    log_activity(
        db=db,
        admin_id=admin_id,
        admin_name=admin_name,
        action=action,
        target_type="MEMBER",
        target_id=clean_id,
        metadata={"new_status": status_update.status.value},
    )

    return get_member_by_id(db, clean_id)
