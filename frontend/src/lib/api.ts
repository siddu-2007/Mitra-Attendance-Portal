import {
  AttendanceStatus,
  BulkAttendanceItem,
  DashboardData,
  Department,
  LoginResult,
  Member,
  StudentAttendanceData,
  StudentTeamData,
} from "./types";

export function getApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "");
  }
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") {
      return "http://localhost:8000/api";
    }
    // In production on deployed domain (e.g. Vercel), route through /api/backend
    return "/api/backend";
  }
  return "http://localhost:8000/api";
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<{ success: boolean; message: string; data: T }> {
  const token = typeof window !== "undefined" ? localStorage.getItem("mithra_auth_token") : null;

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const apiBase = getApiBase();
  const res = await fetch(`${apiBase}${endpoint}`, {
    ...options,
    headers,
  });

  const body = await res.json();

  if (!res.ok) {
    const errorMsg = body.detail || body.message || `HTTP ${res.status}`;
    throw new Error(typeof errorMsg === "object" ? JSON.stringify(errorMsg) : errorMsg);
  }

  return body;
}

export const api = {
  // Dashboard
  getDashboard: () => apiRequest<DashboardData>("/dashboard"),

  // Attendance
  getAttendance: (params?: { date?: string; departmentId?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.date) q.set("date", params.date);
    if (params?.departmentId) q.set("departmentId", params.departmentId);
    if (params?.status) q.set("status", params.status);
    return apiRequest<any[]>(`/attendance?${q.toString()}`);
  },

  recordAttendance: (payload: { memberId: string; date: string; status: AttendanceStatus; departmentId?: string }) =>
    apiRequest("/attendance", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  bulkAttendance: (date: string, records: BulkAttendanceItem[]) =>
    apiRequest("/attendance/bulk", {
      method: "POST",
      body: JSON.stringify({ date, records }),
    }),

  markAllPresent: (date: string, departmentId?: string) =>
    apiRequest("/attendance/mark-all-present", {
      method: "POST",
      body: JSON.stringify({ date, departmentId: departmentId || null }),
    }),

  deleteAttendance: (attendanceId: string) =>
    apiRequest(`/attendance/${attendanceId}`, {
      method: "DELETE",
    }),

  // Members
  getMembers: (params?: { search?: string; department?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.department) q.set("department", params.department);
    if (params?.status) q.set("status", params.status);
    return apiRequest<Member[]>(`/members?${q.toString()}`);
  },

  // Departments
  getDepartments: () => apiRequest<Department[]>("/departments"),

  // Current Admin profile
  getMe: () => apiRequest("/auth/me"),

  // Unified Login (Roll Number or College Email)
  login: (identifier: string, passkey?: string) =>
    apiRequest<LoginResult>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ identifier, passkey }),
    }),

  // Student Portal Operations
  getStudentMe: () => apiRequest<Member>("/student/me"),
  getStudentAttendance: () => apiRequest<StudentAttendanceData>("/student/me/attendance"),
  getStudentTeam: () => apiRequest<StudentTeamData>("/student/me/team"),

  // Reports Export
  exportAttendanceReport: async (format: "csv" | "excel" | "pdf" | "json" = "csv", date?: string) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("mithra_auth_token") : null;
    const headers = new Headers();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    const q = new URLSearchParams();
    q.set("format", format);
    if (date) q.set("date", date);

    const apiBase = getApiBase();
    const res = await fetch(`${apiBase}/reports/daily?${q.toString()}`, {
      headers,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Export failed" }));
      throw new Error(err.detail || `Export failed with HTTP ${res.status}`);
    }
    return res.blob();
  },
};
