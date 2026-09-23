export type AdminRole = "PRESIDENT" | "ADMIN" | "STUDENT" | "UNAUTHORIZED";

export type AdminStatus = "ACTIVE" | "INACTIVE";

export type AttendanceStatus = "PRESENT" | "ABSENT" | "LATE";

export interface AdminProfile {
  uid: string;
  name: string;
  email: string;
  role: AdminRole;
  status: AdminStatus;
  permissions: string[];
  createdAt: string;
  updatedAt: string;
}

export interface Department {
  departmentId: string;
  name: string;
  status?: "ACTIVE" | "INACTIVE";
  totalMembers?: number;
}

export interface Member {
  memberId: string;
  name: string;
  email: string;
  phone?: string;
  departmentId: string;
  departmentName?: string;
  academicYear: string;
  joiningDate: string;
  status: "ACTIVE" | "INACTIVE";
}

export interface AttendanceRecord {
  attendanceId: string;
  memberId: string;
  memberName?: string;
  date: string;
  status: AttendanceStatus;
  departmentId: string;
  departmentName?: string;
  markedBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface DepartmentStat {
  departmentId: string;
  departmentName: string;
  totalMembers: number;
  presentToday: number;
  attendancePercentage: number;
}

export interface DashboardData {
  totalActiveMembers: number;
  todayPresent: number;
  todayAbsent: number;
  todayLate: number;
  todayAttendancePercentage: number;
  monthlyAttendancePercentage: number;
  departmentStatistics: DepartmentStat[];
  recentActivity: Array<{
    logId: string;
    action: string;
    adminName: string;
    timestamp: string;
    metadata?: Record<string, any>;
  }>;
}

export interface BulkAttendanceItem {
  memberId: string;
  status: AttendanceStatus;
}

export interface StudentTeamMember {
  memberId: string;
  name: string;
  email: string;
  academicYear: string;
  isMe: boolean;
  status: string;
}

export interface StudentTeamData {
  departmentId: string;
  departmentName: string;
  totalMembers: number;
  teamMembers: StudentTeamMember[];
}

export interface StudentAttendanceHistoryItem {
  attendanceId: string;
  memberId: string;
  memberName: string;
  date: string;
  status: AttendanceStatus;
  departmentId: string;
  markedBy: string;
  createdAt: string;
}

export interface StudentAttendanceData {
  memberId: string;
  memberName: string;
  departmentId: string;
  departmentName?: string;
  overallAttendancePercentage: number;
  totalSessions: number;
  presentCount: number;
  absentCount: number;
  lateCount: number;
  history: StudentAttendanceHistoryItem[];
}

export interface LoginResult {
  role: AdminRole;
  token: string;
  portalRedirect: string;
  user: any;
}
