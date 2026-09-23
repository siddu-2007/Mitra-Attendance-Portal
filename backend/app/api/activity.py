"""Activity Log and Audit Trail Endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from app.core.firebase import get_db
from app.core.security import get_current_admin
from app.models.activity import ActivityLogModel
from app.schemas.common import APIResponse
from app.services.activity_service import query_activity_logs

router = APIRouter()


@router.get("", response_model=APIResponse[List[ActivityLogModel]], summary="Get Activity Audit Logs")
async def get_activity_logs(
    action: Optional[str] = Query(None, description="Filter by action type (e.g. ATTENDANCE_CREATED)"),
    adminId: Optional[str] = Query(None, description="Filter by admin UID"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    targetType: Optional[str] = Query(None, description="Filter by target type (e.g. MEMBER, ATTENDANCE)"),
    limit: int = Query(50, ge=1, le=500),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Retrieve audit trail of administrative actions.
    Restricted to authorized active administrators.
    """
    logs = query_activity_logs(
        db=db,
        action=action,
        admin_id=adminId,
        date=date,
        target_type=targetType,
        limit=limit,
    )
    return APIResponse(
        success=True,
        message=f"Retrieved {len(logs)} activity log entry(ies).",
        data=[ActivityLogModel(**l) for l in logs],
    )
