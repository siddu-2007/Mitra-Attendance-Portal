"""API routers initialization and aggregation."""

from fastapi import APIRouter
from app.api.activity import router as activity_router
from app.api.analytics import router as analytics_router
from app.api.attendance import router as attendance_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.departments import router as departments_router
from app.api.members import router as members_router
from app.api.reports import router as reports_router
from app.api.student import router as student_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication & Admins"])
api_router.include_router(student_router, prefix="/student", tags=["Student Portal"])
api_router.include_router(members_router, prefix="/members", tags=["Members"])
api_router.include_router(departments_router, prefix="/departments", tags=["Departments"])
api_router.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(activity_router, prefix="/activity", tags=["Activity Logs"])
