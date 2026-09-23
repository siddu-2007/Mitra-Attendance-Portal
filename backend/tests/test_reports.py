"""Reports and File Export tests (JSON, CSV, Excel, PDF)."""

def test_daily_report_json(client, admin_headers):
    client.post("/api/attendance", json={"memberId": "VM001", "date": "2026-09-17", "status": "PRESENT"}, headers=admin_headers)
    response = client.get("/api/reports/daily?date=2026-09-17&format=json", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["reportType"] == "Daily Attendance Report"
    assert len(data["rows"]) >= 1


def test_daily_report_csv_export(client, admin_headers):
    response = client.get("/api/reports/daily?date=2026-09-17&format=csv", headers=admin_headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert len(response.content) > 0


def test_monthly_report_excel_export(client, admin_headers):
    response = client.get("/api/reports/monthly?month=9&year=2026&format=excel", headers=admin_headers)
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers.get("content-type", "")
    assert len(response.content) > 0


def test_member_report_pdf_export(client, admin_headers):
    response = client.get("/api/reports/member?memberId=VM001&format=pdf", headers=admin_headers)
    assert response.status_code == 200
    assert "application/pdf" in response.headers.get("content-type", "")
    assert response.content.startswith(b"%PDF")


def test_department_report_json(client, admin_headers):
    response = client.get("/api/reports/department?format=json", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
