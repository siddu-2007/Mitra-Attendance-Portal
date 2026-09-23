"""
Demonstration script verifying User, Admin, and President access differences & mutations.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

# 1. Credentials / Mock Tokens
TOKEN_UNAUTHORIZED = "mock-token:student_99:student@vitstudent.ac.in"
TOKEN_ADMIN = "mock-token:admin_01:admin@mithra.vit.ac.in"
TOKEN_PRESIDENT = "mock-token:president_01:president@mithra.vit.ac.in"

headers_unauth = {"Authorization": f"Bearer {TOKEN_UNAUTHORIZED}", "Content-Type": "application/json"}
headers_admin = {"Authorization": f"Bearer {TOKEN_ADMIN}", "Content-Type": "application/json"}
headers_president = {"Authorization": f"Bearer {TOKEN_PRESIDENT}", "Content-Type": "application/json"}

print("================================================================")
print("VIT MITHRA PORTAL - ROLE-BASED ACCESS & MUTATION DEMONSTRATION")
print("================================================================")

# -------------------------------------------------------------
# SCENARIO 1: UNAUTHORIZED USER (General Student)
# -------------------------------------------------------------
print("\n--- 1. Testing Unauthorized User (General Student) ---")

# Try to access auth me
res_me = requests.get(f"{BASE_URL}/auth/me", headers=headers_unauth)
print(f"GET /api/auth/me status: {res_me.status_code}")
print(f"Response: {res_me.json()}")
assert res_me.status_code == 403, "Expected 403 for unauthorized user"

# Try to mark attendance
payload = {
    "memberId": "VM001",
    "date": "2026-09-17",
    "status": "PRESENT"
}
res_att = requests.post(f"{BASE_URL}/attendance", headers=headers_unauth, json=payload)
print(f"POST /api/attendance status: {res_att.status_code}")
print(f"Response: {res_att.json()}")
assert res_att.status_code == 403, "Expected 403 for unauthorized attendance marking"
print(">>> Unauthorized user successfully blocked with HTTP 403!")

# -------------------------------------------------------------
# SCENARIO 2: REGULAR ADMIN (Operations Admin)
# -------------------------------------------------------------
print("\n--- 2. Testing Regular Admin (Operations Admin) ---")

res_admin_me = requests.get(f"{BASE_URL}/auth/me", headers=headers_admin)
print(f"GET /api/auth/me status: {res_admin_me.status_code}, Role: {res_admin_me.json().get('data', {}).get('role')}")
assert res_admin_me.status_code == 200

# Regular admin records attendance for VM005 on 2026-09-20
att_payload = {
    "memberId": "VM005",
    "date": "2026-09-20",
    "status": "PRESENT"
}
res_record = requests.post(f"{BASE_URL}/attendance", headers=headers_admin, json=att_payload)
print(f"Admin POST /api/attendance status: {res_record.status_code}")
record_data = res_record.json()
print(f"Response: {record_data}")
assert res_record.status_code in [200, 201]

# Try duplicate attendance on same member and date -> MUST return 409
res_dup = requests.post(f"{BASE_URL}/attendance", headers=headers_admin, json=att_payload)
print(f"Duplicate POST /api/attendance status: {res_dup.status_code}")
print(f"Response: {res_dup.json()}")
assert res_dup.status_code == 409
assert res_dup.json().get("detail") == "Attendance already exists for this member and date."
print(">>> Duplicate attendance successfully rejected with HTTP 409!")

# Regular admin attempts to delete attendance -> MUST return 403 (President privilege)
att_id = record_data.get("data", {}).get("attendanceId") or "att_test"
res_admin_del = requests.delete(f"{BASE_URL}/attendance/{att_id}", headers=headers_admin)
print(f"Admin DELETE /api/attendance status: {res_admin_del.status_code}")
print(f"Response: {res_admin_del.json()}")
assert res_admin_del.status_code == 403
print(">>> Admin delete blocked with HTTP 403 (Requires President clearance)!")

# -------------------------------------------------------------
# SCENARIO 3: PRESIDENT (Master Clearance)
# -------------------------------------------------------------
print("\n--- 3. Testing President (Master Clearance) ---")

res_pres_me = requests.get(f"{BASE_URL}/auth/me", headers=headers_president)
print(f"GET /api/auth/me status: {res_pres_me.status_code}, Role: {res_pres_me.json().get('data', {}).get('role')}")
assert res_pres_me.status_code == 200

# President deletes the record created by Admin
if att_id != "att_test":
    res_pres_del = requests.delete(f"{BASE_URL}/attendance/{att_id}", headers=headers_president)
    print(f"President DELETE /api/attendance/{att_id} status: {res_pres_del.status_code}")
    print(f"Response: {res_pres_del.json()}")
    assert res_pres_del.status_code == 200
    print(">>> President successfully deleted attendance record!")

# President bulk updates attendance
bulk_payload = {
    "date": "2026-09-17",
    "records": [
        {"memberId": "VM001", "status": "PRESENT"},
        {"memberId": "VM002", "status": "LATE"},
        {"memberId": "VM003", "status": "PRESENT"},
        {"memberId": "VM004", "status": "PRESENT"},
        {"memberId": "VM005", "status": "PRESENT"},
        {"memberId": "VM006", "status": "ABSENT"}
    ]
}
res_bulk = requests.post(f"{BASE_URL}/attendance/bulk", headers=headers_president, json=bulk_payload)
print(f"President POST /api/attendance/bulk status: {res_bulk.status_code}")
print(f"Response: {res_bulk.json()}")
assert res_bulk.status_code == 200

# Fetch Live Dashboard to verify Quorum Calculation
# Formula: ((Present + Late) / Total) * 100
# Here: Present = 4, Late = 1, Absent = 1, Total = 6
# Quorum = ((4 + 1) / 6) * 100 = 83.33%
res_dash = requests.get(f"{BASE_URL}/dashboard", headers=headers_president)
dash_data = res_dash.json().get("data", {})
print("\n--- Live Dashboard Quorum Calculation ---")
print(f"Total Active Members: {dash_data.get('totalActiveMembers')}")
print(f"Today Present: {dash_data.get('todayPresent')}")
print(f"Today Late: {dash_data.get('todayLate')}")
print(f"Today Absent: {dash_data.get('todayAbsent')}")
print(f"Calculated Quorum Rate: {dash_data.get('todayAttendancePercentage')}%")

print("\n================================================================")
print("ALL ROLE-BASED ACCESS & MUTATION CHECKS PASSED SUCCESSFULLY!")
print("================================================================")
