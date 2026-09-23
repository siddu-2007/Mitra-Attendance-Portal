"""Service for managing Administrators in Firestore."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from app.core.logging import logger
from app.models.activity import ActivityAction
from app.models.admin import AdminModel, AdminRole, AdminStatus
from app.schemas.admin import AdminCreate, AdminStatusUpdate
from app.services.activity_service import log_activity


def get_admin_by_uid(db: Any, uid: str) -> Optional[Dict[str, Any]]:
    """Retrieve admin profile by Firebase Auth UID."""
    doc = db.collection("admins").document(uid).get()
    if doc.exists:
        return doc.to_dict()
    return None


def create_or_onboard_admin(
    db: Any,
    admin_in: AdminCreate,
    created_by_uid: Optional[str] = None,
    created_by_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Create an administrator document in Firestore."""
    admin_ref = db.collection("admins").document(admin_in.uid)
    existing = admin_ref.get()
    if existing.exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": f"Admin with UID {admin_in.uid} already exists.",
                "error": "ADMIN_ALREADY_EXISTS",
            },
        )

    now = datetime.now(timezone.utc).isoformat()
    permissions = admin_in.permissions or (
        ["all"] if admin_in.role == AdminRole.PRESIDENT else ["mark_attendance", "view_reports"]
    )

    admin_data = AdminModel(
        uid=admin_in.uid,
        name=admin_in.name,
        email=admin_in.email,
        role=admin_in.role,
        status=AdminStatus.ACTIVE,
        permissions=permissions,
        createdAt=now,
        updatedAt=now,
    ).model_dump()

    admin_ref.set(admin_data)

    if created_by_uid and created_by_name:
        log_activity(
            db=db,
            admin_id=created_by_uid,
            admin_name=created_by_name,
            action=ActivityAction.MEMBER_CREATED,
            target_type="ADMIN",
            target_id=admin_in.uid,
            metadata={"email": admin_in.email, "role": admin_in.role},
        )

    return admin_data


def list_all_admins(db: Any) -> List[Dict[str, Any]]:
    """List all registered administrators."""
    docs = db.collection("admins").stream()
    return [d.to_dict() for d in docs]


def update_admin_status(
    db: Any,
    target_uid: str,
    status_update: AdminStatusUpdate,
    performed_by_uid: str,
    performed_by_name: str,
) -> Dict[str, Any]:
    """Activate or deactivate an administrator (President only)."""
    admin_ref = db.collection("admins").document(target_uid)
    doc = admin_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Admin not found", "error": "NOT_FOUND"},
        )

    if target_uid == performed_by_uid and status_update.status == AdminStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "You cannot deactivate your own account.", "error": "SELF_DEACTIVATION"},
        )

    now = datetime.now(timezone.utc).isoformat()
    admin_ref.update({"status": status_update.status.value, "updatedAt": now})

    log_activity(
        db=db,
        admin_id=performed_by_uid,
        admin_name=performed_by_name,
        action=ActivityAction.MEMBER_DEACTIVATED if status_update.status == AdminStatus.INACTIVE else ActivityAction.MEMBER_UPDATED,
        target_type="ADMIN",
        target_id=target_uid,
        metadata={"new_status": status_update.status.value},
    )

    updated_doc = admin_ref.get()
    return updated_doc.to_dict()
