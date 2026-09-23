"""Analytics API tests."""

def test_analytics_response_structure(client, admin_headers):
    # Record some attendance
    client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-08-10", "status": "PRESENT"}, headers=admin_headers)
    client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-08-11", "status": "LATE"}, headers=admin_headers)
    client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-08-12", "status": "ABSENT"}, headers=admin_headers)

    response = client.get("/api/analytics?month=8&year=2026", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]

    assert "overallAttendance" in data
    assert data["overallAttendance"] == 66.67  # (1 present + 1 late) / 3 = 66.67%
    assert isinstance(data["monthlyTrend"], list)
    assert len(data["monthlyTrend"]) >= 1
    assert data["attendanceDistribution"]["present"] == 1
    assert data["attendanceDistribution"]["late"] == 1
    assert data["attendanceDistribution"]["absent"] == 1
