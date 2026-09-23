"""Attendance Recording, Duplicate Rejection, Bulk, and Monthly Calculations tests."""

def test_record_attendance_success(client, admin_headers):
    payload = {
        "memberId": "VM001",
        "date": "2026-09-17",
        "status": "PRESENT",
    }
    response = client.post("/api/attendance", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["memberId"] == "VM001"
    assert data["date"] == "2026-09-17"
    assert data["status"] == "PRESENT"
    assert data["attendanceId"] == "VM001_2026-09-17"


def test_duplicate_attendance_rejected(client, admin_headers):
    """Submitting attendance for existing memberId + date must return 409 with exact detail."""
    payload = {
        "memberId": "VM001",
        "date": "2026-09-17",
        "status": "PRESENT",
    }
    # First record succeeds
    client.post("/api/attendance", json=payload, headers=admin_headers)

    # Second record with same member and date is rejected
    response = client.post("/api/attendance", json=payload, headers=admin_headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "Attendance already exists for this member and date."


def test_query_attendance_filters(client, admin_headers):
    client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-09-15", "status": "PRESENT"}, headers=admin_headers)
    client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-09-16", "status": "ABSENT"}, headers=admin_headers)

    # Filter by date
    resp = client.get("/api/attendance?date=2026-09-15", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
    assert resp.json()["data"][0]["date"] == "2026-09-15"

    # Filter by status
    resp_status = client.get("/api/attendance?status=ABSENT", headers=admin_headers)
    assert resp_status.status_code == 200
    assert any(r["status"] == "ABSENT" for r in resp_status.json()["data"])


def test_bulk_attendance_handling(client, admin_headers):
    # Register VM002
    client.post("/api/members", json={
        "memberId": "VM002",
        "name": "Member Two",
        "email": "m2@vitstudent.ac.in",
        "departmentId": "DEPT_TECH",
        "academicYear": "2nd Year",
        "joiningDate": "2026-01-10",
    }, headers=admin_headers)

    payload = {
        "date": "2026-09-18",
        "records": [
            {"memberId": "VM001", "status": "PRESENT"},
            {"memberId": "VM002", "status": "LATE"},
            {"memberId": "VM999", "status": "PRESENT"},  # Non-existent
        ],
    }
    response = client.post("/api/attendance/bulk", json=payload, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["summary"]["successful"] == 2
    assert data["summary"]["failed"] == 1
    assert "VM001" in data["successful"]
    assert "VM002" in data["successful"]
    assert any(f["memberId"] == "VM999" for f in data["failed"])


def test_mark_all_active_present(client, admin_headers):
    response = client.post("/api/attendance/mark-all-present", json={"date": "2026-09-19"}, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["summary"]["successful"] >= 1


def test_update_attendance_status(client, admin_headers):
    create_resp = client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-09-20", "status": "ABSENT"}, headers=admin_headers)
    att_id = create_resp.json()["data"]["attendanceId"]

    update_resp = client.put(f"/api/attendance/{att_id}", json={"status": "PRESENT"}, headers=admin_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["status"] == "PRESENT"


def test_delete_attendance_restricted_to_president(client, admin_headers, president_headers):
    create_resp = client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-09-21", "status": "LATE"}, headers=admin_headers)
    att_id = create_resp.json()["data"]["attendanceId"]

    # Regular admin receives 403
    del_admin = client.delete(f"/api/attendance/{att_id}", headers=admin_headers)
    assert del_admin.status_code == 403

    # President succeeds
    del_pres = client.delete(f"/api/attendance/{att_id}", headers=president_headers)
    assert del_pres.status_code == 200


def test_monthly_attendance_aggregation(client, admin_headers):
    # Record 4 sessions in September 2026: 2 Present, 1 Late, 1 Absent
    # Expected percentage: (2 + 1) / 4 * 100 = 75.0%
    client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-09-01", "status": "PRESENT"}, headers=admin_headers)
    client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-09-02", "status": "PRESENT"}, headers=admin_headers)
    client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-09-03", "status": "LATE"}, headers=admin_headers)
    client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-09-04", "status": "ABSENT"}, headers=admin_headers)

    response = client.get("/api/attendance/monthly?month=9&year=2026&memberId=VM001", headers=admin_headers)
    assert response.status_code == 200
    rows = response.json()["data"]
    assert len(rows) == 1
    m_row = rows[0]
    assert m_row["memberId"] == "VM001"
    assert m_row["presentDays"] == 2
    assert m_row["lateDays"] == 1
    assert m_row["absentDays"] == 1
    assert m_row["totalAttendanceDays"] == 4
    assert m_row["attendancePercentage"] == 75.0
