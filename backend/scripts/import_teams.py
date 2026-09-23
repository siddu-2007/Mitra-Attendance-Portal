"""Import student members and departments from teams_allocation.xlsx into local_firestore.json."""

import os
import json
import random
from datetime import datetime, timezone
import openpyxl

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
EXCEL_PATH = os.path.join(BACKEND_DIR, "data", "teams_allocation.xlsx")
DB_PATH = os.path.join(BACKEND_DIR, "data", "local_firestore.json")

def main():
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: {EXCEL_PATH} not found.")
        return

    wb = openpyxl.load_workbook(EXCEL_PATH)
    sheet = wb["Sheet3"]

    now_iso = datetime.now(timezone.utc).isoformat()

    # Define Departments matching the team wings
    dept_map = {
        "ai": {
            "departmentId": "dept_ai",
            "name": "Artificial Intelligence",
            "code": "ai",
            "status": "ACTIVE",
            "createdAt": now_iso,
            "updatedAt": now_iso,
        },
        "vc": {
            "departmentId": "dept_vc",
            "name": "Vibecoding",
            "code": "vc",
            "status": "ACTIVE",
            "createdAt": now_iso,
            "updatedAt": now_iso,
        },
        "mk": {
            "departmentId": "dept_mk",
            "name": "Marketing Team",
            "code": "mk",
            "status": "ACTIVE",
            "createdAt": now_iso,
            "updatedAt": now_iso,
        },
        "ic": {
            "departmentId": "dept_ic",
            "name": "Industry Connect",
            "code": "ic",
            "status": "ACTIVE",
            "createdAt": now_iso,
            "updatedAt": now_iso,
        },
    }

    # Load existing database if available to preserve admins
    existing_db = {}
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                existing_db = json.load(f)
        except Exception as e:
            print(f"Warning reading existing DB: {e}")

    admins = existing_db.get("admins", {})
    if "admin_01" not in admins:
        admins["admin_01"] = {
            "uid": "admin_01",
            "name": "Operations Admin",
            "email": "admin@mithra.vit.ac.in",
            "role": "ADMIN",
            "status": "ACTIVE",
            "permissions": ["mark_attendance", "view_reports"],
            "createdAt": now_iso,
            "updatedAt": now_iso,
        }

    # Parse Members from Excel (Only students assigned to the 4 official teams)
    members = {}
    rows = list(sheet.iter_rows(values_only=True))
    for r in rows[1:]:
        regd = str(r[0]).strip() if r[0] else ""
        if not regd or regd == "None":
            continue
        team_code = str(r[3]).strip().lower() if r[3] else ""
        if not team_code or team_code not in dept_map:
            continue
        dept_info = dept_map[team_code]
        name = str(r[1]).strip() if r[1] else "Student"
        branch = str(r[2]).strip() if r[2] else "General"

        members[regd] = {
            "memberId": regd,
            "name": name,
            "email": f"{regd.lower()}@vitstudent.ac.in",
            "branch": branch,
            "departmentId": dept_info["departmentId"],
            "departmentName": dept_info["name"],
            "academicYear": "3rd Year",
            "joiningDate": "2024-08-01",
            "status": "ACTIVE",
            "createdAt": now_iso,
            "updatedAt": now_iso,
        }

    # Generate historical attendance records for the students
    # Dates: 2026-09-10, 2026-09-14, 2026-09-18, 2026-09-21
    past_dates = ["2026-09-10", "2026-09-14", "2026-09-18", "2026-09-21"]
    attendance = {}
    random.seed(42)  # Deterministic seed for reproducible attendance stats

    for date_str in past_dates:
        for regd, m in members.items():
            att_id = f"{regd}_{date_str}"
            # Realistic distribution: ~88% PRESENT, ~8% ABSENT, ~4% LATE
            rand_val = random.random()
            if rand_val < 0.88:
                status = "PRESENT"
            elif rand_val < 0.96:
                status = "ABSENT"
            else:
                status = "LATE"

            attendance[att_id] = {
                "attendanceId": att_id,
                "memberId": regd,
                "memberName": m["name"],
                "date": date_str,
                "status": status,
                "departmentId": m["departmentId"],
                "markedBy": "Operations Admin",
                "notes": None,
                "createdAt": f"{date_str}T10:00:00+00:00",
                "updatedAt": f"{date_str}T10:00:00+00:00",
            }

    # Save to local_firestore.json
    db_store = {
        "admins": admins,
        "departments": dept_map,
        "members": members,
        "attendance": attendance,
    }

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db_store, f, indent=2)

    print(f"Successfully imported:")
    print(f"  - {len(members)} Student Members")
    print(f"  - {len(dept_map)} Department Wings")
    print(f"  - {len(attendance)} Historical Attendance Records across {len(past_dates)} dates")
    print(f"  - Database saved to {DB_PATH}")

if __name__ == "__main__":
    main()
