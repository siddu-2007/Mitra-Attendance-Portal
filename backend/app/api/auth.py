"""Authentication and Administrator Management Endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from app.core.config import settings
from app.core.firebase import get_db
from app.core.rate_limit import limiter
from app.core.security import get_current_admin, require_admin_or_api_key, require_president
from app.models.activity import ActivityAction
from app.models.admin import AdminRole, AdminStatus
from app.schemas.admin import AdminCreate, AdminResponse, AdminStatusUpdate
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.common import APIResponse
from app.services.activity_service import log_activity
from app.services.admin_service import (
    create_or_onboard_admin,
    list_all_admins,
    update_admin_status,
)

router = APIRouter()


@router.post("/login", response_model=APIResponse[LoginResponse], summary="Unified Login for Admins and Students")
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login_user(
    request: Request,
    payload: LoginRequest,
    db: Any = Depends(get_db),
):
    """
    Authenticate either an Administrator or a Student Member using Roll Number or College Email.
    Returns the appropriate clearance role and target portal (/dashboard for admins, /student for students).
    """
    clean_id = payload.identifier.strip().lower()

    # 1. Check Admins
    admin_matches = []
    admins = [a.to_dict() for a in db.collection("admins").stream()]
    for a in admins:
        if a.get("email", "").lower() == clean_id or a.get("uid", "").lower() == clean_id:
            admin_matches.append(a)

    # Support president / admin shortcuts
    if not admin_matches:
        if clean_id in ["president", "president@mithra.vit.ac.in"]:
            admin_matches = [a for a in admins if a.get("role") == "PRESIDENT"]
        elif clean_id in ["admin", "admin@mithra.vit.ac.in"]:
            admin_matches = [a for a in admins if a.get("role") == "ADMIN"]

    if admin_matches:
        admin = admin_matches[0]
        # Enforce passkey validation for all administrators
        expected_passkey = getattr(settings, "ADMIN_PASSKEY", "Mithra2026#")
        if not payload.passkey or payload.passkey.strip() != expected_passkey:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "Invalid administrator clearance passkey.", "error": "INVALID_PASSKEY"}
            )

        if admin.get("status", "").upper() != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"success": False, "message": "Administrator account is inactive.", "error": "ADMIN_INACTIVE"}
            )
        role = admin.get("role", "ADMIN")
        token = f"mock-token:{admin['uid']}:{admin['email']}:{role}:{admin.get('name', 'Admin')}"
        return APIResponse(
            success=True,
            message=f"Authenticated as {role}.",
            data=LoginResponse(
                role=role,
                token=token,
                portalRedirect="/dashboard",
                user=admin,
            )
        )

    # 2. Check Students (Members collection)
    members = [m.to_dict() for m in db.collection("members").stream()]
    member_matches = []
    for m in members:
        if m.get("memberId", "").lower() == clean_id or m.get("email", "").lower() == clean_id:
            member_matches.append(m)

    if member_matches:
        student = member_matches[0]
        if student.get("status", "").upper() != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"success": False, "message": "Your club membership is inactive.", "error": "MEMBER_INACTIVE"}
            )
        token = f"mock-token:{student['memberId']}:{student['email']}:STUDENT:{student.get('name', 'Student')}"
        return APIResponse(
            success=True,
            message=f"Welcome, {student.get('name')}! Accessing Student Portal.",
            data=LoginResponse(
                role="STUDENT",
                token=token,
                portalRedirect="/student",
                user=student,
            )
        )

    # Neither admin nor student found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "success": False,
            "message": f"No registered administrator or student member found with roll number or email '{payload.identifier}'.",
            "error": "USER_NOT_FOUND"
        }
    )


@router.get("/me", response_model=APIResponse[AdminResponse], summary="Get Current Admin Profile")
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def get_my_profile(
    request: Request,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Returns the authenticated administrator's verified profile, role, and permissions.
    Enforces active status.
    """
    # Log login/verification event
    log_activity(
        db=db,
        admin_id=current_admin.get("uid", ""),
        admin_name=current_admin.get("name", "Admin"),
        action=ActivityAction.ADMIN_LOGIN,
        target_type="ADMIN",
        target_id=current_admin.get("uid"),
    )

    return APIResponse(
        success=True,
        message="Administrator authenticated successfully.",
        data=AdminResponse(**current_admin),
    )


@router.get("/admins", response_model=APIResponse[List[AdminResponse]], summary="List All Admins")
async def list_admins(
    current_admin: Dict[str, Any] = Depends(require_president),
    db: Any = Depends(get_db),
):
    """List all registered administrators. Restricted to President."""
    admins = list_all_admins(db)
    return APIResponse(
        success=True,
        message="Administrators retrieved successfully.",
        data=[AdminResponse(**a) for a in admins],
    )


@router.post("/admins", response_model=APIResponse[AdminResponse], summary="Register New Admin")
async def add_new_admin(
    admin_in: AdminCreate,
    current_admin: Dict[str, Any] = Depends(require_president),
    db: Any = Depends(get_db),
):
    """Register a new administrator. Restricted to President."""
    created = create_or_onboard_admin(
        db=db,
        admin_in=admin_in,
        created_by_uid=current_admin.get("uid"),
        created_by_name=current_admin.get("name"),
    )
    return APIResponse(
        success=True,
        message=f"Administrator '{admin_in.name}' created successfully.",
        data=AdminResponse(**created),
    )


@router.patch("/admins/{uid}/status", response_model=APIResponse[AdminResponse], summary="Update Admin Status")
async def change_admin_status(
    uid: str,
    status_in: AdminStatusUpdate,
    current_admin: Dict[str, Any] = Depends(require_president),
    db: Any = Depends(get_db),
):
    """Activate or deactivate an administrator. Restricted to President."""
    updated = update_admin_status(
        db=db,
        target_uid=uid,
        status_update=status_in,
        performed_by_uid=current_admin.get("uid"),
        performed_by_name=current_admin.get("name"),
    )
    return APIResponse(
        success=True,
        message="Administrator status updated.",
        data=AdminResponse(**updated),
    )


@router.post("/setup-president", response_model=APIResponse[AdminResponse], summary="Initial President Setup")
async def setup_initial_president(
    admin_in: AdminCreate,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Any = Depends(get_db),
):
    """
    Bootstrap the initial President account.
    Allowed only if either:
    1. No administrators exist in the database yet, OR
    2. A valid internal X-API-Key header is provided.
    """
    existing_admins = list_all_admins(db)
    api_key_valid = bool(settings.API_KEY and x_api_key == settings.API_KEY)

    if len(existing_admins) > 0 and not api_key_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Administrators already exist. Setup endpoint is locked.",
                "error": "SETUP_LOCKED",
            },
        )

    # Force PRESIDENT role for initial bootstrap
    admin_in.role = AdminRole.PRESIDENT
    admin_in.permissions = ["all"]

    created = create_or_onboard_admin(
        db=db,
        admin_in=admin_in,
        created_by_uid="BOOTSTRAP",
        created_by_name="System Bootstrap",
    )

    return APIResponse(
        success=True,
        message="Initial President account successfully configured.",
        data=AdminResponse(**created),
    )
