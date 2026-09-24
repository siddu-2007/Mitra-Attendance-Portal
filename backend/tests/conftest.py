"""Pytest configuration, fixtures, and mock test clients."""

import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from starlette.testclient import TestClient
from app.core.config import settings
from app.core.firebase import get_db, initialize_firebase
from app.main import app

PRESIDENT_UID = "president_test_01"
ADMIN_UID = "admin_test_01"
INACTIVE_UID = "inactive_test_01"


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure mock firebase environment and clean database before every test."""
    settings.API_KEY = "test_secret_api_key"
    initialize_firebase()
    db = get_db()
    if hasattr(db, "_persist_to_disk"):
        db._persist_to_disk = False
    if hasattr(db, "clear"):
        db.clear()

    # Seed President in admins collection
    db.collection("admins").document(PRESIDENT_UID).set({
        "uid": PRESIDENT_UID,
        "name": "Mithra President",
        "email": "president@mithra.vit.ac.in",
        "role": "PRESIDENT",
        "status": "ACTIVE",
        "permissions": ["all"],
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
    })

    # Seed Admin in admins collection
    db.collection("admins").document(ADMIN_UID).set({
        "uid": ADMIN_UID,
        "name": "Mithra Regular Admin",
        "email": "admin@mithra.vit.ac.in",
        "role": "ADMIN",
        "status": "ACTIVE",
        "permissions": ["mark_attendance", "view_reports"],
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
    })

    # Seed Inactive Admin
    db.collection("admins").document(INACTIVE_UID).set({
        "uid": INACTIVE_UID,
        "name": "Deactivated Admin",
        "email": "inactive@mithra.vit.ac.in",
        "role": "ADMIN",
        "status": "INACTIVE",
        "permissions": [],
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
    })

    # Seed a default Department
    db.collection("departments").document("DEPT_TECH").set({
        "departmentId": "DEPT_TECH",
        "name": "Skill Advancement",
        "status": "ACTIVE",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
    })

    # Seed a default Member
    db.collection("members").document("VM001").set({
        "memberId": "VM001",
        "name": "Aarav Sharma",
        "email": "aarav.sharma@vitstudent.ac.in",
        "phone": "9876543210",
        "departmentId": "DEPT_TECH",
        "academicYear": "2nd Year",
        "joiningDate": "2026-01-10",
        "status": "ACTIVE",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
    })

    yield db


@pytest.fixture
def client():
    """Unauthenticated HTTP TestClient."""
    return TestClient(app)


@pytest.fixture
def president_headers():
    """Headers authenticated as President."""
    return {"Authorization": f"Bearer mock-token:{PRESIDENT_UID}:president@mithra.vit.ac.in"}


@pytest.fixture
def admin_headers():
    """Headers authenticated as Regular Admin."""
    return {"Authorization": f"Bearer mock-token:{ADMIN_UID}:admin@mithra.vit.ac.in"}


@pytest.fixture
def inactive_headers():
    """Headers for deactivated admin."""
    return {"Authorization": f"Bearer mock-token:{INACTIVE_UID}:inactive@mithra.vit.ac.in"}
