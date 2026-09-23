"""Department Management tests."""

def test_list_departments(client, admin_headers):
    response = client.get("/api/departments", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert any(d["name"] == "Skill Advancement" for d in data)


def test_create_department(client, admin_headers):
    payload = {"name": "Public Relations"}
    response = client.post("/api/departments", json=payload, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Public Relations"
    assert response.json()["data"]["status"] == "ACTIVE"


def test_duplicate_active_department_rejected(client, admin_headers):
    payload = {"name": "Skill Advancement"}
    response = client.post("/api/departments", json=payload, headers=admin_headers)
    assert response.status_code == 409
    assert response.json()["error"] == "DUPLICATE_DEPARTMENT"


def test_update_department_name(client, admin_headers):
    # Create temp department to update
    create_resp = client.post("/api/departments", json={"name": "Logistics & Ops"}, headers=admin_headers)
    dept_id = create_resp.json()["data"]["departmentId"]

    update_resp = client.put(f"/api/departments/{dept_id}", json={"name": "Logistics & Operations"}, headers=admin_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["name"] == "Logistics & Operations"


def test_prevent_deactivating_department_with_active_members(client, admin_headers):
    """DEPT_TECH has active member VM001; attempting deactivation should return 400."""
    response = client.patch(
        "/api/departments/DEPT_TECH/status",
        json={"status": "INACTIVE"},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["error"] == "DEPARTMENT_IN_USE"
