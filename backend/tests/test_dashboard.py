"""Consolidated Dashboard API tests."""

from app.utils.validators import get_today_date_str


def test_dashboard_metrics(client, admin_headers):
    today = get_today_date_str()
    # Record today's attendance for VM001
    client.post("/api/attendance", json={"memberId": "VM001", "date": today, "status": "PRESENT"}, headers=admin_headers)

    response = client.get("/api/dashboard", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["totalActiveMembers"] >= 1
    assert data["todayPresent"] >= 1
    assert data["todayAttendancePercentage"] >= 0.0
    assert isinstance(data["departmentStatistics"], list)
    assert len(data["departmentStatistics"]) >= 1
    assert isinstance(data["recentActivity"], list)
