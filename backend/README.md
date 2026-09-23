# VIT Mithra Attendance Portal - Backend

Production-grade, private backend API for the **VIT Mithra Attendance Portal**, built with **Python 3.11+**, **FastAPI**, **Firebase Authentication**, and **Cloud Firestore**.

Designed specifically to power the VIT Mithra club's internal attendance operations, member records, and department analytics, integrating cleanly with the Next.js frontend designed in Stitch.

---

## Architecture Overview

```
backend/
├── app/
│   ├── main.py                     # FastAPI entrypoint, CORS, exception handlers, rate limiter
│   │
│   ├── core/
│   │   ├── config.py               # Pydantic Settings (.env, CORS origins, limits)
│   │   ├── security.py             # Firebase ID token verification, RBAC, API key middleware
│   │   ├── firebase.py             # Firebase Admin SDK init with mock fallback for testing
│   │   ├── logging.py              # Structured application logger with secret masking
│   │   └── rate_limit.py           # Endpoint rate limiting via slowapi
│   │
│   ├── api/
│   │   ├── auth.py                 # Admin profile (/me), onboard new admins, status updates
│   │   ├── members.py              # Member CRUD, search, filters, soft deactivation
│   │   ├── departments.py          # Department CRUD, duplicate prevention, dependency guards
│   │   ├── attendance.py           # Daily, bulk submission, mark-all-present, monthly summary
│   │   ├── dashboard.py            # Optimized single-request dashboard metrics
│   │   ├── analytics.py            # Monthly trends, distribution, department rates
│   │   ├── reports.py              # Tabular reports + CSV, Excel (.xlsx), and PDF exports
│   │   └── activity.py             # Append-only audit trail and activity logging
│   │
│   ├── models/                     # Firestore collection entity models
│   │   ├── admin.py
│   │   ├── member.py
│   │   ├── department.py
│   │   ├── attendance.py
│   │   └── activity.py
│   │
│   ├── schemas/                    # Pydantic validation and API response schemas
│   │   ├── common.py               # Standard API response envelope & error schemas
│   │   ├── admin.py
│   │   ├── member.py
│   │   ├── department.py
│   │   ├── attendance.py
│   │   ├── dashboard.py
│   │   ├── analytics.py
│   │   └── reports.py
│   │
│   ├── services/                   # Business logic layer
│   │   ├── admin_service.py
│   │   ├── member_service.py
│   │   ├── department_service.py
│   │   ├── attendance_service.py
│   │   ├── dashboard_service.py
│   │   ├── analytics_service.py
│   │   ├── report_service.py
│   │   └── activity_service.py
│   │
│   └── utils/                      # Utilities
│       ├── calculations.py         # Attendance percentage & status summarization
│       ├── validators.py           # Date, ID, and month sanitizers
│       └── exporters.py            # CSV, openpyxl Excel, and ReportLab PDF exporters
│
├── tests/                          # Automated Pytest suite (43 test cases)
│   ├── conftest.py                 # Test fixtures, mock database, auth tokens
│   ├── test_health.py              # /health & /docs
│   ├── test_auth.py                # Token verification, 401/403, President RBAC
│   ├── test_members.py             # Member CRUD, uniqueness, soft deactivation
│   ├── test_departments.py         # Department management, duplicate guards
│   ├── test_attendance.py          # Daily, duplicate 409 rejection, bulk, monthly
│   ├── test_calculations.py        # Mathematical accuracy, edge cases
│   ├── test_dashboard.py           # Single-request KPI aggregation
│   ├── test_analytics.py           # Monthly trends, distribution
│   ├── test_reports.py             # Tabular data and CSV/Excel/PDF exports
│   └── test_activity.py            # Activity audit logging
│
├── firestore.rules                 # Cloud Firestore security rules
├── firestore.indexes.json          # Firestore composite indexes
├── requirements.txt                # Pinned dependencies
├── .env.example                    # Environment configuration template
└── README.md                       # Comprehensive guide
```

---

## Key Features & Business Rules

1. **Strictly Private & Authenticated**:
   - Zero public endpoints or registration.
   - All browser requests authenticate via Firebase Authentication ID tokens (`Authorization: Bearer <token>`).
   - Verifies the user against Firestore `admins/{uid}`: checks that `status == "ACTIVE"`. Inactive accounts receive `HTTP 403 Forbidden`.
   - Role-Based Access Control (RBAC): Differentiates between `PRESIDENT` and `ADMIN`.

2. **Deterministic Attendance & Duplicate Prevention**:
   - Document ID pattern: `{memberId}_{YYYY-MM-DD}` (e.g., `VM001_2026-09-17`).
   - Submitting duplicate attendance for the same member and date triggers `HTTP 409 Conflict` with:
     ```json
     {
       "detail": "Attendance already exists for this member and date."
     }
     ```
   - Bulk attendance (`POST /api/attendance/bulk`) and "Mark All Present" support partial failure handling, returning clear summaries of successful, duplicate, and failed records.

3. **Accurate Attendance Math**:
   - Formula: `Attendance Percentage = ((Present Days + Late Days) / Total Attendance Days) * 100`
   - `PRESENT` = counted (1.0)
   - `LATE` = counted (1.0)
   - `ABSENT` = counted (0.0)
   - Rounded to 2 decimal places. 0 sessions safely returns `0.0%`.

4. **Optimized Single-Roundtrip Dashboard (`GET /api/dashboard`)**:
   - Returns total active members, today's present, absent, late counts, today's attendance percentage, monthly percentage, department breakdown, and recent activity logs in one call.

5. **Server-Side File Export (`/api/reports/*`)**:
   - Endpoints support `?format=json`, `?format=csv`, `?format=excel` (styled `.xlsx` with openpyxl), and `?format=pdf` (landscape tables via ReportLab).

6. **Append-Only Activity Audit Trail (`/api/activity`)**:
   - Records all key events: `ADMIN_LOGIN`, `MEMBER_CREATED`, `MEMBER_UPDATED`, `MEMBER_DEACTIVATED`, `ATTENDANCE_CREATED`, `ATTENDANCE_UPDATED`, `DEPARTMENT_CREATED`, `DEPARTMENT_UPDATED`, `REPORT_GENERATED`.

7. **Security & Sensitive Data Masking**:
   - Custom logging filter masks Bearer tokens, private keys, API keys, and passwords.
   - CORS is restricted to explicit `FRONTEND_URL` origins.
   - Rate limiting on sensitive endpoints (login, bulk attendance, reports).

---

## Requirements

- **Python**: 3.11 or higher
- **pip**: 24.0+
- **Firebase Project**: With Authentication and Firestore enabled.

---

## Local Setup & Installation

### 1. Clone & Enter Backend Directory

```bash
cd "backend"
```

### 2. Create and Activate Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Populate the `.env` file with your credentials:

```ini
ENVIRONMENT=development
PORT=8000
DEBUG=True

# Firebase Service Account Credentials
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="your_firebase_private_key_here"
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com

# Backend API Key for Internal Service Operations
API_KEY=your_secure_backend_api_key_here

# Frontend CORS Origin (comma-separated if multiple)
FRONTEND_URL=http://localhost:3000,http://127.0.0.1:3000
```

> **Note on Local Development without live Firebase**:
> If you have not created your Firebase project yet, the backend automatically runs with an **in-memory Firestore & Token mock emulator**. You can run tests and inspect Swagger docs immediately!

---

## Firebase Setup Guide

### 1. Create Firebase Project
1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Click **Add project** and name it (e.g., `vit-mithra-attendance`).

### 2. Enable Authentication
1. Navigate to **Build > Authentication > Sign-in method**.
2. Enable **Email/Password**.
3. Create administrator user accounts in the **Users** tab (e.g. `president@mithra.vit.ac.in`, `admin@mithra.vit.ac.in`).

### 3. Enable Cloud Firestore
1. Navigate to **Build > Firestore Database**.
2. Click **Create database** (start in production mode).
3. Select your preferred region (e.g., `asia-south1` for Mumbai, India).
4. Deploy the security rules from `firestore.rules` and indexes from `firestore.indexes.json` using Firebase CLI:
   ```bash
   firebase deploy --only firestore:rules,firestore:indexes
   ```

### 4. Generate Service Account Private Key
1. Go to **Project Settings > Service accounts**.
2. Click **Generate new private key**.
3. Download the JSON file.
4. Copy `project_id`, `client_email`, and `private_key` into your `.env` file.

---

## Initial Admin Onboarding (Bootstrap)

To initialize your first President account in Firestore without manual database editing:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/setup-president \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_secure_backend_api_key_here" \
  -d '{
    "uid": "YOUR_FIREBASE_AUTH_UID",
    "name": "Club President",
    "email": "president@mithra.vit.ac.in",
    "role": "PRESIDENT"
  }'
```

Once administrators exist, this endpoint automatically locks itself from public access.

---

## Running the Backend

Start the development server with Uvicorn:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **API Base URL**: `http://127.0.0.1:8000/api`
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`
- **Health Check**: `http://127.0.0.1:8000/health`

---

## Running Automated Tests

Run the complete test suite:

```bash
pytest -v tests/
```

All 43 unit and integration tests run in under 1 second:

```
tests/test_activity.py::test_activity_logging_flow PASSED
tests/test_analytics.py::test_analytics_response_structure PASSED
tests/test_attendance.py::test_record_attendance_success PASSED
tests/test_attendance.py::test_duplicate_attendance_rejected PASSED
tests/test_attendance.py::test_query_attendance_filters PASSED
tests/test_attendance.py::test_bulk_attendance_handling PASSED
tests/test_attendance.py::test_mark_all_active_present PASSED
tests/test_attendance.py::test_update_attendance_status PASSED
tests/test_attendance.py::test_delete_attendance_restricted_to_president PASSED
tests/test_attendance.py::test_monthly_attendance_aggregation PASSED
tests/test_auth.py::test_unauthorized_access_fails PASSED
tests/test_auth.py::test_invalid_bearer_token PASSED
tests/test_auth.py::test_inactive_admin_blocked PASSED
tests/test_auth.py::test_active_admin_authenticated PASSED
tests/test_auth.py::test_president_permission_enforced PASSED
tests/test_auth.py::test_president_can_add_admin PASSED
tests/test_auth.py::test_duplicate_admin_rejected PASSED
tests/test_calculations.py::test_zero_total_days PASSED
tests/test_calculations.py::test_full_attendance PASSED
tests/test_calculations.py::test_present_and_late_counted PASSED
tests/test_calculations.py::test_rounding_two_decimal_places PASSED
tests/test_calculations.py::test_status_summarization PASSED
tests/test_dashboard.py::test_dashboard_metrics PASSED
tests/test_departments.py::test_list_departments PASSED
tests/test_departments.py::test_create_department PASSED
tests/test_departments.py::test_duplicate_active_department_rejected PASSED
tests/test_departments.py::test_update_department_name PASSED
tests/test_departments.py::test_prevent_deactivating_department_with_active_members PASSED
tests/test_health.py::test_health_check PASSED
tests/test_health.py::test_docs_available PASSED
tests/test_health.py::test_redoc_available PASSED
tests/test_members.py::test_list_members PASSED
tests/test_members.py::test_create_member_success PASSED
tests/test_members.py::test_duplicate_member_id_rejected PASSED
tests/test_members.py::test_create_member_invalid_department PASSED
tests/test_members.py::test_update_member PASSED
tests/test_members.py::test_soft_deactivation PASSED
tests/test_members.py::test_member_search_filter PASSED
tests/test_reports.py::test_daily_report_json PASSED
tests/test_reports.py::test_daily_report_csv_export PASSED
tests/test_reports.py::test_monthly_report_excel_export PASSED
tests/test_reports.py::test_member_report_pdf_export PASSED
tests/test_reports.py::test_department_report_json PASSED
```

---

## API Endpoints Reference

### 1. Health & Docs
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/health` | Service health status | No |
| `GET` | `/docs` | Interactive Swagger UI | No |
| `GET` | `/redoc` | OpenAPI ReDoc | No |

### 2. Authentication & Admin Operations (`/api/auth`)
| Method | Endpoint | Description | Role Required |
|---|---|---|---|
| `GET` | `/api/auth/me` | Fetch verified admin profile | Active Admin |
| `GET` | `/api/auth/admins` | List all registered admins | President |
| `POST` | `/api/auth/admins` | Add new admin account | President |
| `PATCH` | `/api/auth/admins/{uid}/status` | Activate / deactivate admin | President |
| `POST` | `/api/auth/setup-president` | Initial bootstrap endpoint | API Key or Empty DB |

### 3. Member Management (`/api/members`)
| Method | Endpoint | Description | Role Required |
|---|---|---|---|
| `GET` | `/api/members` | List members (search, dept, status, year) | Active Admin |
| `POST` | `/api/members` | Register new member | Active Admin |
| `GET` | `/api/members/{member_id}` | Get member profile | Active Admin |
| `PUT` | `/api/members/{member_id}` | Update member details | Active Admin |
| `PATCH` | `/api/members/{member_id}/status` | Soft deactivate / activate | Active Admin |
| `GET` | `/api/members/{member_id}/attendance`| Member attendance history & overall % | Active Admin |

### 4. Department Management (`/api/departments`)
| Method | Endpoint | Description | Role Required |
|---|---|---|---|
| `GET` | `/api/departments` | List all departments | Active Admin |
| `POST` | `/api/departments` | Create department (unique name) | Active Admin |
| `GET` | `/api/departments/{id}` | Get department details | Active Admin |
| `PUT` | `/api/departments/{id}` | Update department name | Active Admin |
| `PATCH` | `/api/departments/{id}/status` | Toggle active/inactive status | Active Admin |

### 5. Attendance Operations (`/api/attendance`)
| Method | Endpoint | Description | Role Required |
|---|---|---|---|
| `POST` | `/api/attendance` | Record daily attendance (409 on duplicate) | Active Admin |
| `GET` | `/api/attendance` | Filter attendance by date, dept, member, status | Active Admin |
| `POST` | `/api/attendance/bulk` | Bulk attendance submission | Active Admin |
| `POST` | `/api/attendance/mark-all-present` | Mark all active members present | Active Admin |
| `GET` | `/api/attendance/monthly` | Monthly attendance % breakdown | Active Admin |
| `GET` | `/api/attendance/{id}` | Get attendance record | Active Admin |
| `PUT` | `/api/attendance/{id}` | Update attendance record | Active Admin |
| `DELETE` | `/api/attendance/{id}` | Delete attendance record | President |

### 6. Dashboard & Analytics
| Method | Endpoint | Description | Role Required |
|---|---|---|---|
| `GET` | `/api/dashboard` | Unified KPIs, today breakdown, recent logs | Active Admin |
| `GET` | `/api/analytics` | Overall %, monthly trend, distribution | Active Admin |

### 7. Reports & Exports (`/api/reports`)
| Method | Endpoint | Description | Formats Supported |
|---|---|---|---|
| `GET` | `/api/reports/daily` | Daily attendance report | `json`, `csv`, `excel`, `pdf` |
| `GET` | `/api/reports/monthly` | Monthly attendance report | `json`, `csv`, `excel`, `pdf` |
| `GET` | `/api/reports/member` | Individual member dossier | `json`, `csv`, `excel`, `pdf` |
| `GET` | `/api/reports/department` | Department comparison report | `json`, `csv`, `excel`, `pdf` |

### 8. Audit Trail (`/api/activity`)
| Method | Endpoint | Description | Role Required |
|---|---|---|---|
| `GET` | `/api/activity` | Query audit trail (action, admin, date) | Active Admin |

---

## Frontend Integration Guide (Next.js)

The Next.js frontend connects to FastAPI using Firebase Authentication ID tokens.

### 1. Next.js Client-Side Auth & API Helper (`lib/api.ts`)

```typescript
// frontend/lib/api.ts
import { getAuth } from "firebase/auth";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000/api";

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const auth = getAuth();
  const user = auth.currentUser;

  if (!user) {
    throw new Error("User not authenticated.");
  }

  // Get fresh Firebase ID Token
  const token = await user.getIdToken();

  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${token}`);
  headers.set("Content-Type", "application/json");

  const response = await fetch(`${BACKEND_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || data.detail || "API Request Failed");
  }

  return data;
}
```

### 2. Loading the Dashboard in Next.js

```typescript
// In your Dashboard component
import { useEffect, useState } from "react";
import { fetchWithAuth } from "@/lib/api";

export default function DashboardPage() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const res = await fetchWithAuth("/dashboard");
        setDashboardData(res.data);
      } catch (err) {
        console.error("Failed to load dashboard:", err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  if (loading) return <div>Loading portal...</div>;

  return (
    <div>
      <h1>Today's Attendance: {dashboardData.todayAttendancePercentage}%</h1>
      <p>Active Members: {dashboardData.totalActiveMembers}</p>
      <p>Present: {dashboardData.todayPresent} | Absent: {dashboardData.todayAbsent} | Late: {dashboardData.todayLate}</p>
    </div>
  );
}
```

### 3. Submitting Bulk Attendance

```typescript
export async function submitBulkAttendance(date: string, records: { memberId: string; status: string }[]) {
  return await fetchWithAuth("/attendance/bulk", {
    method: "POST",
    body: JSON.stringify({ date, records }),
  });
}
```

### 4. Downloading Export Reports (CSV / Excel / PDF)

```typescript
export async function downloadReport(reportType: "daily" | "monthly", format: "csv" | "excel" | "pdf", queryParams: string = "") {
  const auth = getAuth();
  const token = await auth.currentUser?.getIdToken();

  const url = `${BACKEND_URL}/reports/${reportType}?format=${format}&${queryParams}`;
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = `mithra_${reportType}_report.${format === "excel" ? "xlsx" : format}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}
```

---

## Production Deployment Checklist

1. **Environment Variables**:
   - Ensure `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, and `FIREBASE_PRIVATE_KEY` are configured securely in your cloud hosting environment (e.g. Google Cloud Run, AWS ECS, Railway).
   - Set `DEBUG=False`.
   - Set `FRONTEND_URL` to your production Next.js domain (e.g., `https://mithra.vit.ac.in`).
   - Set `API_KEY` to a cryptographically secure 64-character token.

2. **Deploying on Google Cloud Run**:
   ```bash
   gcloud run deploy mithra-backend \
     --source . \
     --platform managed \
     --region asia-south1 \
     --allow-unauthenticated \
     --set-env-vars ENVIRONMENT=production,DEBUG=False,FRONTEND_URL=https://mithra.vit.ac.in
   ```

3. **Firestore Indexes & Security Rules**:
   Deploy rules and composite indexes to your live Firebase project:
   ```bash
   firebase deploy --only firestore:rules,firestore:indexes
   ```
