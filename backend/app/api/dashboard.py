"""Single-Request Consolidated Dashboard Endpoint."""

from typing import Any, Dict
from fastapi import APIRouter, Depends
from app.core.firebase import get_db
from app.core.security import get_current_admin
from app.schemas.common import APIResponse
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import get_dashboard_metrics

router = APIRouter()


@router.get("", response_model=APIResponse[DashboardResponse], summary="Get Dashboard Overview")
async def get_dashboard(
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Optimized consolidated endpoint powering the main Next.js dashboard in a single round-trip.
    Provides total active members, today's breakdown, monthly percentage,
    department statistics, and recent activity logs.
    """
    metrics = get_dashboard_metrics(db=db)
    return APIResponse(
        success=True,
        message="Dashboard metrics loaded successfully.",
        data=metrics,
    )
