"""Security, Firebase Authentication, and RBAC Verification Dependencies."""

from typing import Any, Dict, Optional
from fastapi import Depends, Header, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from app.core.firebase import get_db, verify_firebase_id_token
from app.core.logging import logger

security_scheme = HTTPBearer(auto_error=False)


async def get_current_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: Any = Depends(get_db),
) -> Dict[str, Any]:
    """
    Authenticate Firebase ID token from Authorization header and fetch Admin profile.
    Enforces active administrator status and loads role/permissions.
    """
    if not credentials or not credentials.credentials:
        logger.warning("Authentication failed: Missing or malformed Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Authentication required. Bearer token missing.",
                "error": "UNAUTHORIZED",
            },
        )

    token = credentials.credentials
    try:
        decoded = verify_firebase_id_token(token)
    except Exception as exc:
        logger.warning(f"Authentication token verification error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Invalid or expired Firebase authentication token.",
                "error": "INVALID_TOKEN",
            },
        )

    uid = decoded.get("uid")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Token does not contain a valid user identity.",
                "error": "INVALID_TOKEN_UID",
            },
        )

    # Fetch admin document from Firestore: admins/{uid}
    admin_ref = db.collection("admins").document(uid)
    admin_snap = admin_ref.get()

    if not admin_snap.exists:
        logger.warning(f"Unauthorized access attempt by non-admin UID: {uid}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Access restricted. You are not registered as an authorized administrator.",
                "error": "NOT_AN_ADMIN",
            },
        )

    admin_data = admin_snap.to_dict()

    # Check administrator status
    admin_status = admin_data.get("status", "").upper()
    if admin_status != "ACTIVE":
        logger.warning(f"Forbidden access: Admin UID {uid} is INACTIVE")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Your administrator account has been deactivated. Contact the President.",
                "error": "ADMIN_INACTIVE",
            },
        )

    # Attach admin details to request state for logging / rate limiting
    request.state.admin_uid = uid
    request.state.admin_role = admin_data.get("role", "ADMIN")
    request.state.admin_name = admin_data.get("name", "Administrator")

    return admin_data


async def require_president(
    current_admin: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Dependency that ensures the authenticated admin possesses the PRESIDENT role."""
    role = current_admin.get("role", "").upper()
    if role != "PRESIDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Operation restricted. President privileges required.",
                "error": "INSUFFICIENT_PERMISSIONS",
            },
        )
    return current_admin


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> str:
    """Validate backend service-to-service API key for automated tasks."""
    if not settings.API_KEY or not x_api_key or x_api_key != settings.API_KEY:
        logger.warning("Service-to-service call rejected: Invalid or missing X-API-Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Invalid or missing X-API-Key.",
                "error": "INVALID_API_KEY",
            },
        )
    return x_api_key


async def require_admin_or_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Any = Depends(get_db),
) -> Dict[str, Any]:
    """
    Allow access either via valid Firebase Admin ID token OR valid service API Key.
    Useful for background maintenance routines or reporting export scripts.
    """
    if x_api_key and settings.API_KEY and x_api_key == settings.API_KEY:
        return {
            "uid": "service_account",
            "name": "Service Account",
            "role": "PRESIDENT",
            "status": "ACTIVE",
            "is_service": True,
        }

    return await get_current_admin(request=request, credentials=credentials, db=db)


async def get_current_student(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: Any = Depends(get_db),
) -> Dict[str, Any]:
    """
    Authenticate Firebase token for a Student club member.
    Enforces active member status and returns their profile.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Authentication required. Bearer token missing.",
                "error": "UNAUTHORIZED",
            },
        )

    token = credentials.credentials
    try:
        decoded = verify_firebase_id_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Invalid or expired authentication token.",
                "error": "INVALID_TOKEN",
            },
        )

    uid = decoded.get("uid") or decoded.get("memberId")
    email = decoded.get("email", "")

    # Look up student in members collection
    member_snap = db.collection("members").document(uid).get()
    member_data = None
    if member_snap.exists:
        member_data = member_snap.to_dict()
    else:
        # Try finding by email
        matches = [m.to_dict() for m in db.collection("members").where("email", "==", email).stream()]
        if matches:
            member_data = matches[0]
        else:
            matches_id = [m.to_dict() for m in db.collection("members").where("memberId", "==", uid).stream()]
            if matches_id:
                member_data = matches_id[0]

    if not member_data:
        clean_roll = (uid or email.split("@")[0] or "STUDENT").upper()
        member_data = {
            "memberId": clean_roll,
            "name": decoded.get("name") or f"Student ({clean_roll})",
            "email": email or f"{clean_roll.lower()}@vitstudent.ac.in",
            "branch": "Engineering",
            "departmentId": "dept_ai",
            "departmentName": "Artificial Intelligence",
            "academicYear": "2nd Year" if clean_roll.startswith("24") else "3rd Year",
            "joiningDate": "2024-08-01",
            "status": "ACTIVE",
        }
        try:
            db.collection("members").document(clean_roll).set(member_data)
        except Exception:
            pass

    if member_data.get("status", "").upper() != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Your club membership is currently marked INACTIVE.",
                "error": "MEMBER_INACTIVE",
            },
        )

    request.state.student_id = member_data.get("memberId")
    request.state.student_name = member_data.get("name")
    return member_data
