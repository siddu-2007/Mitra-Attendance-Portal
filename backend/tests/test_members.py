"""Member Management tests."""

def test_list_members(client, admin_headers):
    """Retrieve members list."""
    response = client.get("/api/members", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 1
    assert any(m["memberId"] == "VM001" for m in data)


def test_create_member_success(client, admin_headers):
    """Register a valid new member."""
    payload = {
        "memberId": "VM002",
        "name": "Ananya Reddy",
        "email": "ananya.reddy@vitstudent.ac.in",
        "phone": "9123456780",
        "departmentId": "DEPT_TECH",
        "academicYear": "3rd Year",
        "joiningDate": "2026-01-15",
    }
    response = client.post("/api/members", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["memberId"] == "VM002"
    assert data["status"] == "ACTIVE"


def test_duplicate_member_id_rejected(client, admin_headers):
    """Attempting to register an existing memberId returns 409."""
    payload = {
        "memberId": "VM001",
        "name": "Duplicate Aarav",
        "email": "aarav.duplicate@vitstudent.ac.in",
        "departmentId": "DEPT_TECH",
        "academicYear": "2nd Year",
        "joiningDate": "2026-01-10",
    }
    response = client.post("/api/members", json=payload, headers=admin_headers)
    assert response.status_code == 409
    assert response.json()["error"] == "DUPLICATE_MEMBER_ID"


def test_create_member_invalid_department(client, admin_headers):
    """Member creation with non-existent department returns 404."""
    payload = {
        "memberId": "VM003",
        "name": "Invalid Dept Member",
        "email": "invalid@vitstudent.ac.in",
        "departmentId": "NON_EXISTENT_DEPT",
        "academicYear": "1st Year",
        "joiningDate": "2026-02-01",
    }
    response = client.post("/api/members", json=payload, headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["error"] == "INVALID_DEPARTMENT"


def test_update_member(client, admin_headers):
    """Update member's phone and academicYear."""
    payload = {"phone": "9998887776", "academicYear": "Final Year"}
    response = client.put("/api/members/VM001", json=payload, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["phone"] == "9998887776"
    assert data["academicYear"] == "Final Year"


def test_soft_deactivation(client, admin_headers):
    """Soft deactivation sets status to INACTIVE without removing the record."""
    response = client.patch("/api/members/VM001/status", json={"status": "INACTIVE"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "INACTIVE"

    # Confirm member is still queryable
    get_resp = client.get("/api/members/VM001", headers=admin_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["status"] == "INACTIVE"


def test_member_search_filter(client, admin_headers):
    """Search by partial name or ID."""
    response = client.get("/api/members?search=Aarav", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1
