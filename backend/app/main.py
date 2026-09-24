"""VIT Mithra Attendance Portal - Main FastAPI Application Entrypoint."""

import os
from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api import api_router
from app.core.config import settings
from app.core.logging import logger
from app.core.rate_limit import limiter
from app.schemas.common import APIErrorResponse
from datetime import datetime, timezone
from app.core.firebase import get_db, initialize_firebase, is_mock_mode

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown event handler."""
    logger.info("Initializing VIT Mithra Attendance Portal Backend...")
    initialize_firebase()
    mode = "MOCK / IN-MEMORY" if is_mock_mode() else "LIVE FIREBASE FIRESTORE"
    logger.info(f"Database driver active: {mode}")
    logger.info(f"Allowed CORS origins: {settings.cors_origins}")

    if is_mock_mode():
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()
        # Seed President
        pres_ref = db.collection("admins").document("president_01")
        if not pres_ref.get().exists:
            pres_ref.set({
                "uid": "president_01",
                "name": "Club President",
                "email": "president@mithra.vit.ac.in",
                "role": "PRESIDENT",
                "status": "ACTIVE",
                "permissions": ["all"],
                "createdAt": now_iso,
                "updatedAt": now_iso,
            })
        # Seed Admin
        admin_ref = db.collection("admins").document("admin_01")
        if not admin_ref.get().exists:
            admin_ref.set({
                "uid": "admin_01",
                "name": "Operations Admin",
                "email": "admin@mithra.vit.ac.in",
                "role": "ADMIN",
                "status": "ACTIVE",
                "permissions": ["mark_attendance", "view_reports"],
                "createdAt": now_iso,
                "updatedAt": now_iso,
            })
        # Seed from teams_allocation.xlsx if members collection is empty
        members_count = len(list(db.collection("members").stream()))
        if members_count == 0:
            excel_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "teams_allocation.xlsx"))
            if os.path.exists(excel_path):
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(excel_path)
                    sheet = wb["Sheet3"]
                    dept_map = {
                        "ai": {"departmentId": "ai", "name": "Artificial Intelligence", "code": "ai", "status": "ACTIVE", "createdAt": now_iso, "updatedAt": now_iso},
                        "vc": {"departmentId": "vc", "name": "Vibecoding", "code": "vc", "status": "ACTIVE", "createdAt": now_iso, "updatedAt": now_iso},
                        "mk": {"departmentId": "mk", "name": "Marketing Team", "code": "mk", "status": "ACTIVE", "createdAt": now_iso, "updatedAt": now_iso},
                        "ic": {"departmentId": "ic", "name": "Industry Connect", "code": "ic", "status": "ACTIVE", "createdAt": now_iso, "updatedAt": now_iso},
                    }
                    for d_id, d_data in dept_map.items():
                        db.collection("departments").document(d_id).set(d_data)

                    for r in list(sheet.iter_rows(values_only=True))[1:]:
                        regd = str(r[0]).strip() if r[0] else ""
                        if not regd or regd == "None":
                            continue
                        t_code = str(r[3]).strip().lower() if r[3] else ""
                        if not t_code or t_code not in dept_map:
                            continue
                        d_info = dept_map[t_code]
                        name = str(r[1]).strip() if r[1] else "Student"
                        branch = str(r[2]).strip() if r[2] else "General"
                        db.collection("members").document(regd).set({
                            "memberId": regd,
                            "name": name,
                            "email": f"{regd.lower()}@vitstudent.ac.in",
                            "branch": branch,
                            "departmentId": d_info["departmentId"],
                            "departmentName": d_info["name"],
                            "academicYear": "3rd Year",
                            "joiningDate": "2024-08-01",
                            "status": "ACTIVE",
                            "createdAt": now_iso,
                            "updatedAt": now_iso,
                        })
                    logger.info("Auto-seeded student members from teams_allocation.xlsx")
                except Exception as ex:
                    logger.warning(f"Could not auto-seed from teams_allocation.xlsx: {ex}")

    yield
    logger.info("Shutting down VIT Mithra Attendance Portal Backend.")


# Initialize FastAPI application
app = FastAPI(
    title="VIT Mithra Attendance Portal API",
    description="Production-grade private backend API for VIT Mithra Club Attendance and Administrator Operations.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Attach rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# -----------------------------------------------------------------------------
# Global Exception Handlers for Consistent JSON Responses
# -----------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Format HTTPExceptions into the standard API error envelope."""
    if isinstance(exc.detail, dict):
        content = dict(exc.detail)
        if "detail" not in content and "message" in content:
            content["detail"] = content["message"]
        return JSONResponse(status_code=exc.status_code, content=content)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "detail": str(exc.detail),
            "error": f"HTTP_{exc.status_code}",
            "details": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic request validation errors gracefully."""
    errors = exc.errors()
    formatted_errors = []
    for err in errors:
        loc = " -> ".join([str(l) for l in err.get("loc", [])])
        msg = err.get("msg", "Invalid value")
        formatted_errors.append(f"{loc}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Request validation failed. Please check your inputs.",
            "error": "VALIDATION_ERROR",
            "details": formatted_errors,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions without leaking stack traces or secrets."""
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=settings.DEBUG)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred. Please contact the administrator.",
            "error": "INTERNAL_SERVER_ERROR",
            "details": str(exc) if settings.DEBUG else None,
        },
    )


# -----------------------------------------------------------------------------
# CORS Middleware
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "Accept"],
    expose_headers=["Content-Disposition", "Content-Type"],
)


# -----------------------------------------------------------------------------
# Health Check Endpoint
# -----------------------------------------------------------------------------
@app.get("/health", tags=["Health"], summary="System Health Check")
@app.get("/api/health", tags=["Health"], include_in_schema=False)
@app.get("/api/backend/health", tags=["Health"], include_in_schema=False)
async def health_check() -> Dict[str, str]:
    """Simple health check verifying backend availability without exposing sensitive config."""
    return {"status": "healthy"}


# Mount all API routes under API_V1_PREFIX (/api)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
# Also mount under /api/backend to seamlessly support Vercel multi-service routing
app.include_router(api_router, prefix="/api/backend")


# -----------------------------------------------------------------------------
# Frontend Stitch UI Preview Endpoints & Navigation Hub
# -----------------------------------------------------------------------------
STITCH_CODE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "stitch_screens", "code")
)


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to UI navigation hub."""
    return RedirectResponse(url="/ui")


@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
async def ui_hub():
    """Interactive navigation hub for Stitch frontend screens and backend docs."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIT Mithra Attendance Portal - Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>body { font-family: 'Plus Jakarta Sans', sans-serif; }</style>
</head>
<body class="bg-slate-50 text-slate-900 min-h-screen flex flex-col items-center justify-center p-6">
    <div class="max-w-xl w-full bg-white rounded-2xl shadow-xl border border-slate-200/80 p-8">
        <div class="flex items-center gap-3 mb-6">
            <div class="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-600 text-2xl font-bold">
                M
            </div>
            <div>
                <h1 class="text-2xl font-bold text-slate-900">VIT Mithra Portal</h1>
                <p class="text-sm text-slate-500">Attendance System &amp; Telemetry Console</p>
            </div>
            <span class="ml-auto px-2.5 py-1 text-xs font-semibold uppercase tracking-wider text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full">Active</span>
        </div>

        <p class="text-sm text-slate-600 mb-6">Click any screen below to open the live Stitch design or test the FastAPI backend endpoints directly:</p>

        <div class="space-y-3">
            <a href="/ui/dashboard" class="flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-amber-400 hover:bg-amber-50/40 transition-all group">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center font-bold">📊</div>
                    <div>
                        <div class="font-semibold text-slate-800 group-hover:text-amber-800">1. Executive Dashboard</div>
                        <div class="text-xs text-slate-500">Quorum telemetry, bento metrics, department rates</div>
                    </div>
                </div>
                <span class="text-slate-400 group-hover:text-amber-600 font-bold">&rarr;</span>
            </a>

            <a href="/ui/attendance" class="flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-amber-400 hover:bg-amber-50/40 transition-all group">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">📋</div>
                    <div>
                        <div class="font-semibold text-slate-800 group-hover:text-amber-800">2. Daily Attendance</div>
                        <div class="text-xs text-slate-500">Roll call, mark all present, quick stats &amp; search</div>
                    </div>
                </div>
                <span class="text-slate-400 group-hover:text-amber-600 font-bold">&rarr;</span>
            </a>

            <a href="/ui/login" class="flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-amber-400 hover:bg-amber-50/40 transition-all group">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center font-bold">🔐</div>
                    <div>
                        <div class="font-semibold text-slate-800 group-hover:text-amber-800">3. Admin Login</div>
                        <div class="text-xs text-slate-500">University credentials &amp; master clearance portal</div>
                    </div>
                </div>
                <span class="text-slate-400 group-hover:text-amber-600 font-bold">&rarr;</span>
            </a>

            <div class="pt-4 border-t border-slate-100 flex gap-3">
                <a href="/docs" class="flex-1 text-center py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-all">
                    Swagger API Docs
                </a>
                <a href="/redoc" class="flex-1 text-center py-2.5 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-semibold transition-all">
                    ReDoc Reference
                </a>
            </div>
        </div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@app.get("/ui/dashboard", include_in_schema=False)
async def ui_dashboard():
    file_path = os.path.join(STITCH_CODE_DIR, "executive_dashboard.html")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Screen file not found.")


@app.get("/ui/attendance", include_in_schema=False)
async def ui_attendance():
    file_path = os.path.join(STITCH_CODE_DIR, "daily_attendance.html")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Screen file not found.")


@app.get("/ui/login", include_in_schema=False)
async def ui_login():
    file_path = os.path.join(STITCH_CODE_DIR, "admin_login.html")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Screen file not found.")

