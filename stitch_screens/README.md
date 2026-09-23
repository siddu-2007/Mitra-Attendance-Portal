# VIT Mithra Attendance Portal - Stitch Screen Mapping & Integration

This directory contains the original UI design assets and HTML code downloaded directly from **Stitch Project `6032253794026234771`**.

---

## Downloaded Assets Summary

| Screen Title | Stitch Screen ID | Local Screenshot | Local HTML Code | Backend API Endpoint |
|---|---|---|---|---|
| **1. Executive Dashboard (Light)** | `6f603a2cc10346b1a938e10966732042` | `stitch_screens/images/executive_dashboard.png` | `stitch_screens/code/executive_dashboard.html` | `GET /api/dashboard` & `GET /api/analytics` |
| **2. Daily Attendance (Light)** | `85241b26a2314191bef249e20085930a` | `stitch_screens/images/daily_attendance.png` | `stitch_screens/code/daily_attendance.html` | `GET /api/attendance`, `POST /api/attendance/bulk`, `POST /api/attendance/mark-all-present` |
| **3. Admin Login (Light)** | `7cdff4d0d8784b62bcd9824ff3522226` | `stitch_screens/images/admin_login.png` | `stitch_screens/code/admin_login.html` | Firebase Auth + `GET /api/auth/me` |

---

## 1. Executive Dashboard Screen Integration

### Visual Components on Stitch Screen:
- **Header**: "VIT Mithra Admin Attendance Portal" with status pill.
- **Top Date Pill**: e.g., `17 SEP 2026`.
- **2x2 Bento Matrix**:
  - **Present Today**: count (e.g. `41`), delta badge, quorum percentage.
  - **Absent Today**: count (e.g. `07`), approved duty leaves count.
  - **Monthly Avg**: cumulative percentage (e.g. `88.2%`), target comparison (`+3.2% vs Target`).
- **Live Quorum Status**:
  - High-end circular SVG radial gauge showing current percentage rate (`85.4%`).
  - Legend breakdown: Present count & percentage, Absent count & percentage.
  - Quick action: "Open Daily Attendance Roll" button.
- **Attendance Velocity**: Weekly/monthly trend curve (`7D`, `30D`, `3M` time controls).
- **Department Overview**:
  - Unit list (e.g., *Skill Advancement*, *Technical Events Wing*, *Design & Media Cell*).
  - Enrolled member count, attendance count (`17/18 Present`), percentage badge (`94.4%`), and visual progress bar.

### Corresponding Backend Endpoint:
```http
GET /api/dashboard
Authorization: Bearer <firebase_id_token>
```
**Response Mapping**:
- `todayPresent` ➔ "Present Today" card
- `todayAbsent` ➔ "Absent Today" card
- `todayAttendancePercentage` ➔ Radial gauge & quorum percentage
- `monthlyAttendancePercentage` ➔ "Monthly Avg" card
- `totalActiveMembers` ➔ Total active club strength
- `departmentStatistics` ➔ "Department Overview" cards with member counts and progress bars
- `recentActivity` ➔ Telemetry audit log list

For trend curves across `7d`, `30d`, and `3m`:
```http
GET /api/analytics
Authorization: Bearer <firebase_id_token>
```
Returns `monthlyTrend` array and `overallAttendance`.

---

## 2. Daily Attendance Screen Integration

### Visual Components on Stitch Screen:
- **Date Pill Selector**: Selects date (defaults to today `YYYY-MM-DD`).
- **Department Filter**: Dropdown filtering roster by department.
- **Quick Stat Bar**: `#stat-present` (e.g. `5 / 6`) and `#stat-absent` (e.g. `1 / 6`).
- **Search Bar**: `#member-search` searching name or memberId (e.g. `VM001`).
- **Action Buttons**:
  - **"Mark All Present"** button (`#mark-all-present-btn`).
  - **"Discard"** button (`#discard-btn`).
  - **"Save"** button (`#save-btn`) with server sync toast notification.
- **Member Cards**:
  - Member Avatar, Name, Member ID badge (`VM001`), Department subtitle.
  - Status badge: Present (`check_circle`), Absent (`cancel`), or Late (`schedule`).
  - 2-Way / 3-Way quick toggle buttons (`Present` / `Absent` / `Late`).

### Corresponding Backend Endpoints:

1. **Fetch Members / Today's Sheet**:
   ```http
   GET /api/attendance?date=2026-09-17
   Authorization: Bearer <firebase_id_token>
   ```
   Or fetch active member roster:
   ```http
   GET /api/members?status=ACTIVE
   Authorization: Bearer <firebase_id_token>
   ```

2. **Mark All Present**:
   ```http
   POST /api/attendance/mark-all-present
   Authorization: Bearer <firebase_id_token>
   Content-Type: application/json

   {
     "date": "2026-09-17",
     "departmentId": null
   }
   ```

3. **Save Unsaved Changes (Bulk Attendance)**:
   ```http
   POST /api/attendance/bulk
   Authorization: Bearer <firebase_id_token>
   Content-Type: application/json

   {
     "date": "2026-09-17",
     "records": [
       { "memberId": "VM001", "status": "PRESENT" },
       { "memberId": "VM002", "status": "ABSENT" },
       { "memberId": "VM003", "status": "PRESENT" }
     ]
   }
   ```

---

## 3. Admin Login Screen Integration

### Visual Components on Stitch Screen:
- **Insignia**: VIT Mithra insignia with golden glow.
- **Badges**: "VIT MITHRA", "Admin Secure Access", "256-Bit TLS".
- **Form Fields**:
  - **University Credentials**: Email input (`#adminEmail`), e.g., `admin.mithra@vitstudent.ac.in`.
  - **Master Passcode**: Password input (`#adminPass`) with eye toggle icon.
  - **Remember Session**: Checkbox (30d persistence).
- **Submit Button**: "Authenticate & Enter" (`#authSubmitBtn`).
- **Biometrics Option**: Campus TrustKey pairing.
- **Success Toast**: "Admin Verified - Access granted. Launching Executive Dashboard...".

### Corresponding Flow:
1. **Next.js Client Login**:
   Calls Firebase Client Auth SDK:
   ```typescript
   import { getAuth, signInWithEmailAndPassword } from "firebase/auth";
   const auth = getAuth();
   const userCredential = await signInWithEmailAndPassword(auth, email, password);
   const idToken = await userCredential.user.getIdToken();
   ```
2. **FastAPI Verification**:
   ```http
   GET /api/auth/me
   Authorization: Bearer <idToken>
   ```
3. If verified and active, router pushes to `/dashboard`.
