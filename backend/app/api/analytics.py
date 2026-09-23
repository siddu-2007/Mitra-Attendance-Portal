"""Analytics and Trend Reporting Endpoints."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query
from app.core.firebase import get_db
from app.core.security import get_current_admin
from app.schemas.analytics import AnalyticsResponse
from app.schemas.common import APIResponse
from app.services.analytics_service import get_analytics_data

router = APIRouter()


@router.get("", response_model=APIResponse[AnalyticsResponse], summary="Get Attendance Analytics")
async def get_analytics(
    department: Optional[str] = Query(None, description="Filter by department ID"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month (1-12)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Year (e.g. 2026)"),
    startDate: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    endDate: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Any = Depends(get_db),
):
    """
    Returns aggregated analytics: overall attendance percentage, chronological monthly trend,
    department statistics, and attendance distribution (present, absent, late).
    """
    analytics = get_analytics_data(
        db=db,
        department_id=department,
        month=month,
        year=year,
        start_date=startDate,
        end_date=endDate,
    )
    return APIResponse(
        success=True,
        message="Analytics calculated successfully.",
        data=analytics,
    )
