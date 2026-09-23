"""Activity and Audit Log tests."""

def test_activity_logging_flow(client, admin_headers):
    # Perform member creation and attendance to generate logs
    client.post("/api/members", json={
        "memberId": "VM010",
        "name": "Audit Test Member",
        "email": "audit@vitstudent.ac.in",
        "departmentId": "DEPT_TECH",
        "academicYear": "1st Year",
        "joiningDate": "2026-01-01",
    }, headers=admin_headers)

    client.post("/api/attendance", json={
        "memberId": "VM010",
        "date": "2026-09-17",
        "status": "PRESENT",
    }, headers=admin_headers)

    response = client.get("/api/activity", headers=admin_headers)
    assert response.status_code == 200
    logs = response.json()["data"]
    assert len(logs) >= 2
    actions = [l["action"] for l in logs]
    assert "MEMBER_CREATED" in actions
    assert "ATTENDANCE_CREATED" in actions
