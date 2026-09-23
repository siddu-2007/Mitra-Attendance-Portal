"""Authentication, Authorization, and RBAC tests."""

def test_unauthorized_access_fails(client):
    """Accessing protected endpoint without token returns HTTP 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "UNAUTHORIZED"


def test_invalid_bearer_token(client):
    """Non-existent or bad token returns HTTP 401 or 403."""
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer mock-token:unknown_uid"})
    assert response.status_code == 403
    data = response.json()
    assert data["error"] == "NOT_AN_ADMIN"


def test_inactive_admin_blocked(client, inactive_headers):
    """Deactivated administrators receive HTTP 403 Forbidden."""
    response = client.get("/api/auth/me", headers=inactive_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error"] == "ADMIN_INACTIVE"


def test_active_admin_authenticated(client, admin_headers):
    """Active administrator successfully authenticated."""
    response = client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "admin@mithra.vit.ac.in"
    assert data["data"]["role"] == "ADMIN"


def test_president_permission_enforced(client, admin_headers, president_headers):
    """Regular admin cannot list or manage admins; President can."""
    # Regular admin receives 403
    resp_admin = client.get("/api/auth/admins", headers=admin_headers)
    assert resp_admin.status_code == 403
    assert resp_admin.json()["error"] == "INSUFFICIENT_PERMISSIONS"

    # President receives 200
    resp_pres = client.get("/api/auth/admins", headers=president_headers)
    assert resp_pres.status_code == 200
    assert resp_pres.json()["success"] is True
    assert len(resp_pres.json()["data"]) >= 2


def test_president_can_add_admin(client, president_headers):
    """President can onboard a new administrator."""
    payload = {
        "uid": "new_admin_99",
        "name": "Kavya Patel",
        "email": "kavya.patel@mithra.vit.ac.in",
        "role": "ADMIN",
        "permissions": ["mark_attendance"],
    }
    response = client.post("/api/auth/admins", json=payload, headers=president_headers)
    assert response.status_code == 200
    assert response.json()["data"]["uid"] == "new_admin_99"


def test_duplicate_admin_rejected(client, president_headers):
    """Cannot register admin with duplicate UID."""
    payload = {
        "uid": "admin_test_01",
        "name": "Duplicate Admin",
        "email": "duplicate@mithra.vit.ac.in",
        "role": "ADMIN",
    }
    response = client.post("/api/auth/admins", json=payload, headers=president_headers)
    assert response.status_code == 409
    assert response.json()["error"] == "ADMIN_ALREADY_EXISTS"
