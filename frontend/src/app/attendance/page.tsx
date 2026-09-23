"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { AttendanceStatus, Department, Member } from "@/lib/types";
import { useAuth } from "@/lib/auth-context";
import { downloadAttendanceReport } from "@/lib/export-utils";

interface MemberAttendanceState {
  member: Member;
  status: AttendanceStatus;
  isModified: boolean;
  attendanceId?: string;
}

export interface SavedSessionSummary {
  date: string;
  totalRecords: number;
  presentCount: number;
  absentCount: number;
  lateCount: number;
  markedBy?: string;
  percentage: number;
}

export default function AttendancePage() {
  const { role, student } = useAuth();

  // State
  const [date, setDate] = useState<string>(() => {
    if (typeof window !== "undefined") {
      const p = new URLSearchParams(window.location.search).get("date");
      if (p) return p;
    }
    const today = new Date();
    return today.toISOString().split("T")[0];
  });
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDeptId, setSelectedDeptId] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [roster, setRoster] = useState<MemberAttendanceState[]>([]);
  const [initialRoster, setInitialRoster] = useState<MemberAttendanceState[]>([]);
  const [savedSessions, setSavedSessions] = useState<SavedSessionSummary[]>([]);
  const [showSessionsDrawer, setShowSessionsDrawer] = useState(false);
  const [toast, setToast] = useState<{ show: boolean; title: string; message: string; type: "success" | "error" | "warning" }>({
    show: false,
    title: "",
    message: "",
    type: "success",
  });

  const [isExporting, setIsExporting] = useState(false);

  const showFeedback = (title: string, message: string, type: "success" | "error" | "warning" = "success") => {
    setToast({ show: true, title, message, type });
    setTimeout(() => {
      setToast((prev) => ({ ...prev, show: false }));
    }, 4000);
  };

  const handleExport = async (targetDate: string, format: "csv" | "excel" = "csv") => {
    setIsExporting(true);
    try {
      await downloadAttendanceReport(targetDate || date, format, roster);
      showFeedback(
        format === "excel" ? "Excel Spreadsheet Exported" : "CSV Attendance Exported",
        `Attendance file for ${targetDate || date} is ready. Compatible with Microsoft Excel and folders.`,
        "success"
      );
    } catch (err: any) {
      showFeedback("Export Error", err.message || "Failed to download attendance file", "error");
    } finally {
      setIsExporting(false);
    }
  };

  // Load Data
  const loadData = async () => {
    setLoading(true);
    try {
      // 1. Fetch departments
      try {
        const deptRes = await api.getDepartments();
        if (deptRes.data && deptRes.data.length > 0) {
          setDepartments(deptRes.data);
        } else {
          setDepartments([
            { departmentId: "dept_01", name: "Skill Advancement", totalMembers: 18 },
            { departmentId: "dept_02", name: "Technical Events Wing", totalMembers: 16 },
            { departmentId: "dept_03", name: "Design & Media Cell", totalMembers: 14 },
          ]);
        }
      } catch (e) {
        setDepartments([
          { departmentId: "dept_01", name: "Skill Advancement", totalMembers: 18 },
          { departmentId: "dept_02", name: "Technical Events Wing", totalMembers: 16 },
          { departmentId: "dept_03", name: "Design & Media Cell", totalMembers: 14 },
        ]);
      }

      // 2. Fetch members
      let memberList: Member[] = [];
      try {
        const memRes = await api.getMembers();
        if (memRes.data && memRes.data.length > 0) {
          memberList = memRes.data;
        }
      } catch (e) {
        console.warn("Using fallback member list");
      }

      // If memberList is empty and API failed, keep empty array
      if (memberList.length === 0) {
        memberList = [];
      }

      // 3. Fetch existing attendance for this date
      let existingAttendance: Record<string, { status: AttendanceStatus; id: string }> = {};
      try {
        const attRes = await api.getAttendance({ date });
        if (attRes.data) {
          attRes.data.forEach((rec: any) => {
            existingAttendance[rec.memberId] = {
              status: rec.status,
              id: rec.attendanceId,
            };
          });
        }
      } catch (e) {
        console.warn("Using default attendance state");
      }

      const initial: MemberAttendanceState[] = memberList.map((m, idx) => {
        const exist = existingAttendance[m.memberId];
        return {
          member: m,
          status: exist ? exist.status : idx === 1 ? "ABSENT" : "PRESENT",
          isModified: false,
          attendanceId: exist?.id,
        };
      });

      setRoster(initial);
      setInitialRoster(JSON.parse(JSON.stringify(initial)));

      // 4. Fetch all sessions summary across past dates
      try {
        const allAttRes = await api.getAttendance();
        if (allAttRes.data && allAttRes.data.length > 0) {
          const grouped: Record<string, { total: number; p: number; a: number; l: number; markedBy: string }> = {};
          allAttRes.data.forEach((rec: any) => {
            const d = rec.date;
            if (!grouped[d]) {
              grouped[d] = { total: 0, p: 0, a: 0, l: 0, markedBy: rec.markedByName || "Operations Admin" };
            }
            grouped[d].total += 1;
            if (rec.status === "PRESENT") grouped[d].p += 1;
            else if (rec.status === "ABSENT") grouped[d].a += 1;
            else if (rec.status === "LATE") grouped[d].l += 1;
          });

          const sessionList: SavedSessionSummary[] = Object.entries(grouped)
            .map(([d, g]) => ({
              date: d,
              totalRecords: g.total,
              presentCount: g.p,
              absentCount: g.a,
              lateCount: g.l,
              markedBy: g.markedBy,
              percentage: g.total > 0 ? (g.p / g.total) * 100 : 0,
            }))
            .sort((a, b) => b.date.localeCompare(a.date));

          setSavedSessions(sessionList);
        }
      } catch (e) {
        console.warn("Could not calculate sessions history:", e);
      }
    } catch (err: any) {
      showFeedback("Error Loading Roster", err.message || "Failed to load data", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [date, role]);

  // Status Change
  const handleToggleStatus = (memberId: string, newStatus: AttendanceStatus) => {
    setRoster((prev) =>
      prev.map((item) => {
        if (item.member.memberId === memberId) {
          return {
            ...item,
            status: newStatus,
            isModified: true,
          };
        }
        return item;
      })
    );
  };

  // Mark all filtered present
  const handleMarkAllPresent = () => {
    setRoster((prev) =>
      prev.map((item) => {
        const matchesDept = selectedDeptId === "ALL" || item.member.departmentId === selectedDeptId;
        if (matchesDept) {
          return {
            ...item,
            status: "PRESENT",
            isModified: true,
          };
        }
        return item;
      })
    );
    showFeedback("Staged", "Filtered members marked PRESENT. Click 'Save Attendance' to persist.", "success");
  };

  // Discard changes
  const handleDiscard = () => {
    setRoster(JSON.parse(JSON.stringify(initialRoster)));
    showFeedback("Changes Reverted", "Unsaved modifications have been reset.", "warning");
  };

  // Commit Save
  const handleSave = async () => {
    setSaving(true);
    try {
      const recordsToSave = roster.map((item) => ({
        memberId: item.member.memberId,
        status: item.status,
      }));

      const res = await api.bulkAttendance(date, recordsToSave);
      showFeedback("Attendance Saved to Server", res.message || "Attendance recorded successfully!", "success");

      const savedState = roster.map((item) => ({ ...item, isModified: false }));
      setRoster(savedState);
      setInitialRoster(JSON.parse(JSON.stringify(savedState)));

      // Refresh saved sessions history
      try {
        const allAttRes = await api.getAttendance();
        if (allAttRes.data && allAttRes.data.length > 0) {
          const grouped: Record<string, { total: number; p: number; a: number; l: number; markedBy: string }> = {};
          allAttRes.data.forEach((rec: any) => {
            const d = rec.date;
            if (!grouped[d]) {
              grouped[d] = { total: 0, p: 0, a: 0, l: 0, markedBy: rec.markedByName || "Operations Admin" };
            }
            grouped[d].total += 1;
            if (rec.status === "PRESENT") grouped[d].p += 1;
            else if (rec.status === "ABSENT") grouped[d].a += 1;
            else if (rec.status === "LATE") grouped[d].l += 1;
          });

          const sessionList: SavedSessionSummary[] = Object.entries(grouped)
            .map(([d, g]) => ({
              date: d,
              totalRecords: g.total,
              presentCount: g.p,
              absentCount: g.a,
              lateCount: g.l,
              markedBy: g.markedBy,
              percentage: g.total > 0 ? (g.p / g.total) * 100 : 0,
            }))
            .sort((a, b) => b.date.localeCompare(a.date));

          setSavedSessions(sessionList);
        }
      } catch (e) {
        console.warn("Could not refresh session summary after save");
      }
    } catch (err: any) {
      const msg = err.message || "Failed to save attendance";
      if (msg.includes("already exists") || msg.includes("409")) {
        showFeedback("Duplicate Attendance (HTTP 409)", "Attendance already exists for this date.", "error");
      } else if (msg.includes("403") || msg.includes("permission") || msg.includes("Forbidden")) {
        showFeedback(
          "Access Denied (HTTP 403)",
          "Unauthorized! You do not have permissions to mark attendance. Switch role in top header.",
          "error"
        );
      } else {
        showFeedback("Save Failed", msg, "error");
      }
    } finally {
      setSaving(false);
    }
  };

  // Delete attendance record (President-only privilege)
  const handleDeleteAttendance = async (attendanceId?: string, memberName?: string) => {
    if (role !== "PRESIDENT") {
      showFeedback("President Clearance Required", "Only the President can delete existing attendance records.", "error");
      return;
    }
    if (!attendanceId) {
      showFeedback("No Remote Record", "This entry has not yet been saved with a server attendance ID.", "warning");
      return;
    }

    try {
      await api.deleteAttendance(attendanceId);
      showFeedback("Record Deleted", `Attendance for ${memberName || "member"} deleted successfully.`, "success");
      loadData();
    } catch (err: any) {
      showFeedback("Delete Failed", err.message || "Could not delete attendance record.", "error");
    }
  };

  // Filtered Roster
  const filteredRoster = useMemo(() => {
    return roster.filter((item) => {
      const matchesDept = selectedDeptId === "ALL" || item.member.departmentId === selectedDeptId;
      const matchesSearch =
        searchQuery.trim() === "" ||
        item.member.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.member.memberId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.member.email.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesDept && matchesSearch;
    });
  }, [roster, selectedDeptId, searchQuery]);

  // Aggregate Counts
  const counts = useMemo(() => {
    const presentCount = roster.filter((r) => r.status === "PRESENT").length;
    const absentCount = roster.filter((r) => r.status === "ABSENT").length;
    const lateCount = roster.filter((r) => r.status === "LATE").length;
    const modifiedCount = roster.filter((r) => r.isModified).length;
    const rate = roster.length > 0 ? (presentCount / roster.length) * 100 : 0;
    return { presentCount, absentCount, lateCount, modifiedCount, rate };
  }, [roster]);

  const changeDateByDays = (days: number) => {
    const d = new Date(date);
    d.setDate(d.getDate() + days);
    setDate(d.toISOString().split("T")[0]);
  };

  return (
    <div className="bg-[#F8FAFC] font-sans text-[#0F172A] flex flex-col min-h-screen">
      <Header />

      {/* Floating Toast Notification */}
      {toast.show && (
        <div className="fixed top-20 right-8 z-50 max-w-md w-full animate-fadeIn">
          <div
            className={`p-4 rounded-2xl shadow-2xl flex items-center gap-3 border ${
              toast.type === "success"
                ? "bg-[#0F172A] text-white border-slate-800"
                : toast.type === "warning"
                ? "bg-amber-900 text-amber-50 border-amber-800"
                : "bg-rose-950 text-rose-50 border-rose-800"
            }`}
          >
            <span
              className={`material-symbols-outlined text-2xl ${
                toast.type === "success"
                  ? "text-emerald-400"
                  : toast.type === "warning"
                  ? "text-amber-400"
                  : "text-rose-400"
              }`}
            >
              {toast.type === "success" ? "task_alt" : toast.type === "warning" ? "info" : "error"}
            </span>
            <div className="flex flex-col text-xs">
              <span className="font-bold text-sm">{toast.title}</span>
              <span className="opacity-90 mt-0.5">{toast.message}</span>
            </div>
          </div>
        </div>
      )}

      <main className="flex-1 w-full pt-20 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {/* Top Header & Operational Controls */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 py-4 border-b border-slate-200/80 mb-6">
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500 font-mono-metric mb-1">
              <span>VIT MITHRA</span>
              <span>/</span>
              <span>OPERATIONS</span>
              <span>/</span>
              <span className="text-amber-600 font-semibold">DAILY ROLL</span>
            </div>
            <h1 className="font-headline text-2xl lg:text-3xl font-bold text-slate-900 tracking-tight">
              Daily Attendance Roll
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Record, verify, and synchronize club member attendance for official university compliance.
            </p>
          </div>

          {/* Date Picker & Shortcuts */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center bg-white border border-slate-200 rounded-xl shadow-xs p-1">
              <button
                onClick={() => changeDateByDays(-1)}
                className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-600 transition-colors"
                title="Previous Day"
              >
                <span className="material-symbols-outlined text-lg">chevron_left</span>
              </button>

              <div className="flex items-center gap-2 px-3 py-1">
                <span className="material-symbols-outlined text-amber-600 text-base">calendar_month</span>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="text-xs font-semibold text-slate-800 bg-transparent outline-none cursor-pointer font-mono-metric"
                />
              </div>

              <button
                onClick={() => changeDateByDays(1)}
                className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-600 transition-colors"
                title="Next Day"
              >
                <span className="material-symbols-outlined text-lg">chevron_right</span>
              </button>
            </div>

            <button
              onClick={() => setDate(new Date().toISOString().split("T")[0])}
              className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors"
            >
              Today
            </button>

            {/* Quick Session Date Selector */}
            {savedSessions.length > 0 && (
              <div className="flex items-center">
                <select
                  value={savedSessions.some((s) => s.date === date) ? date : ""}
                  onChange={(e) => {
                    if (e.target.value) setDate(e.target.value);
                  }}
                  className="px-3 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 text-xs font-semibold outline-none cursor-pointer hover:bg-slate-50 transition-colors font-mono-metric shadow-xs"
                >
                  <option value="" disabled>
                    Jump to Session ({savedSessions.length})...
                  </option>
                  {savedSessions.map((s) => (
                    <option key={s.date} value={s.date}>
                      {s.date} ({s.presentCount}P / {s.absentCount}A • {s.percentage.toFixed(0)}%)
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Export CSV Button */}
            <button
              type="button"
              onClick={() => handleExport(date, "csv")}
              disabled={isExporting}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-xs font-semibold shadow-xs hover:border-slate-300 transition-colors disabled:opacity-60"
              title="Download UTF-8 BOM CSV compatible with Microsoft Excel and Windows folders"
            >
              <span className="material-symbols-outlined text-base text-emerald-600">
                {isExporting ? "hourglass_empty" : "download"}
              </span>
              <span>{isExporting ? "Exporting..." : "Export CSV"}</span>
            </button>

            {/* Export Excel (.xlsx) Button */}
            <button
              type="button"
              onClick={() => handleExport(date, "excel")}
              disabled={isExporting}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-800 text-xs font-semibold shadow-xs transition-colors disabled:opacity-60"
              title="Download formatted Microsoft Excel (.xlsx) workbook"
            >
              <span className="material-symbols-outlined text-base text-emerald-700">
                table_view
              </span>
              <span>Excel</span>
            </button>

            <button
              type="button"
              onClick={() => setShowSessionsDrawer(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-300 text-amber-900 text-xs font-semibold shadow-xs transition-colors"
            >
              <span className="material-symbols-outlined text-base text-amber-600">history</span>
              <span>Saved Sessions ({savedSessions.length})</span>
            </button>

            {/* Save Button */}
            <button
              onClick={handleSave}
              disabled={saving}
              className={`flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold shadow-sm transition-all active:scale-[0.98] ${
                counts.modifiedCount > 0
                  ? "bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white shadow-amber-500/25 ring-2 ring-amber-400"
                  : "bg-slate-900 hover:bg-slate-800 text-white"
              }`}
            >
              <span className="material-symbols-outlined text-base">
                {saving ? "sync" : "cloud_upload"}
              </span>
              <span>
                {saving ? "Saving..." : counts.modifiedCount > 0 ? `Save (${counts.modifiedCount} Staged)` : "Save Roll"}
              </span>
            </button>
          </div>
        </div>

        {/* Security & Access Notices */}
        {role === "STUDENT" && (
          <div className="mb-6 p-4 rounded-2xl bg-sky-50 border border-sky-200 flex items-center justify-between text-sky-900 text-xs">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-sky-600 text-xl">school</span>
              <div>
                <strong className="font-semibold">Student Account Active ({student?.name || "Student"} • Roll: {student?.memberId || ""}):</strong> Daily attendance rolls are marked by Club Administrators. Visit your personal portal to review your personal records and team.
              </div>
            </div>
            <Link
              href="/student"
              className="px-3 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-mono-metric font-bold text-xs shrink-0 flex items-center gap-1"
            >
              <span>Open Student Portal</span>
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </Link>
          </div>
        )}

        {role === "UNAUTHORIZED" && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-between text-rose-900 text-xs">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-rose-600 text-xl">block</span>
              <div>
                <strong className="font-semibold">Student Mode Restricted:</strong> You are viewing in read-only mode. Attendance
                submission will trigger an HTTP 403 Forbidden rejection. Switch clearance in the top-right profile menu.
              </div>
            </div>
            <span className="px-2 py-0.5 rounded-full bg-rose-200 text-rose-900 font-mono-metric font-bold text-[11px]">
              READ ONLY
            </span>
          </div>
        )}

        {role === "PRESIDENT" && (
          <div className="mb-6 p-3 rounded-2xl bg-amber-50 border border-amber-200/80 flex items-center justify-between text-amber-900 text-xs">
            <div className="flex items-center gap-2.5">
              <span className="material-symbols-outlined text-amber-700 text-lg">admin_panel_settings</span>
              <span>
                <strong>President Master Mode Active:</strong> You have elevated privileges including individual attendance deletion and override rights.
              </span>
            </div>
          </div>
        )}

        {/* Quick KPI Bar across the top of table */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-500 font-medium">Total Roster</span>
              <div className="font-mono-metric text-2xl font-bold text-slate-900 mt-1">{roster.length}</div>
            </div>
            <div className="w-9 h-9 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center">
              <span className="material-symbols-outlined text-xl">groups</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-500 font-medium">Present Today</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="font-mono-metric text-2xl font-bold text-emerald-600">{counts.presentCount}</span>
                <span className="font-mono-metric text-xs text-emerald-700 font-semibold">
                  ({counts.rate.toFixed(1)}%)
                </span>
              </div>
            </div>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-xl">how_to_reg</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-500 font-medium">Absent</span>
              <div className="font-mono-metric text-2xl font-bold text-rose-600 mt-1">{counts.absentCount}</div>
            </div>
            <div className="w-9 h-9 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-xl">person_off</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-500 font-medium">Staged Changes</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="font-mono-metric text-2xl font-bold text-amber-600">{counts.modifiedCount}</span>
                {counts.modifiedCount > 0 && (
                  <span className="text-[11px] text-amber-700 font-semibold animate-pulse">Unsaved</span>
                )}
              </div>
            </div>
            <div className="w-9 h-9 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-xl">edit_note</span>
            </div>
          </div>
        </div>

        {/* Laptop Filter & Search Toolbar */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] mb-6 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Department Filter Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-1">
            <button
              onClick={() => setSelectedDeptId("ALL")}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                selectedDeptId === "ALL"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              All Wings ({roster.length})
            </button>
            {departments.map((dept) => {
              const count = roster.filter((r) => r.member.departmentId === dept.departmentId).length;
              return (
                <button
                  key={dept.departmentId}
                  onClick={() => setSelectedDeptId(dept.departmentId)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                    selectedDeptId === dept.departmentId
                      ? "bg-amber-500 text-white shadow-xs"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {dept.name} ({count})
                </button>
              );
            })}
          </div>

          {/* Search Input & Bulk Actions */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative min-w-[260px] flex-1 sm:flex-initial">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">
                search
              </span>
              <input
                type="text"
                placeholder="Search member name or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:border-amber-500 focus:bg-white transition-all text-slate-900 placeholder:text-slate-400"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Quick Bulk Action */}
            <button
              onClick={handleMarkAllPresent}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs font-semibold transition-colors"
            >
              <span className="material-symbols-outlined text-base text-emerald-600">done_all</span>
              <span>Mark All Present</span>
            </button>

            {counts.modifiedCount > 0 && (
              <button
                onClick={handleDiscard}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors"
              >
                <span className="material-symbols-outlined text-base text-slate-500">undo</span>
                <span>Reset</span>
              </button>
            )}
          </div>
        </div>

        {/* Laptop Enterprise Attendance Table */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-mono-metric font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3.5 px-6">Member Profile</th>
                  <th className="py-3.5 px-6">Department &amp; Year</th>
                  <th className="py-3.5 px-6">Student Email</th>
                  <th className="py-3.5 px-6">Current Status</th>
                  <th className="py-3.5 px-6 text-center">Quick Toggle Roll</th>
                  {role === "PRESIDENT" && <th className="py-3.5 px-6 text-right">Clearance</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-500">
                      <div className="flex items-center justify-center gap-2">
                        <span className="material-symbols-outlined animate-spin text-amber-500">progress_activity</span>
                        <span>Loading active member roster...</span>
                      </div>
                    </td>
                  </tr>
                ) : filteredRoster.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-500">
                      No club members match the current filter or search criteria.
                    </td>
                  </tr>
                ) : (
                  filteredRoster.map((item) => {
                    const isPresent = item.status === "PRESENT";
                    const isAbsent = item.status === "ABSENT";
                    const isLate = item.status === "LATE";

                    return (
                      <tr
                        key={item.member.memberId}
                        className={`hover:bg-slate-50/80 transition-colors ${
                          item.isModified ? "bg-amber-50/30" : ""
                        }`}
                      >
                        {/* Member Profile */}
                        <td className="py-3.5 px-6">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-slate-900 text-amber-400 font-headline font-bold flex items-center justify-center text-sm shadow-xs shrink-0">
                              {item.member.name.charAt(0)}
                            </div>
                            <div>
                              <div className="font-headline text-sm font-bold text-slate-900 flex items-center gap-2">
                                <span>{item.member.name}</span>
                                {item.isModified && (
                                  <span className="text-[10px] bg-amber-100 text-amber-800 font-mono-metric px-1.5 py-0.2 rounded">
                                    Modified
                                  </span>
                                )}
                              </div>
                              <span className="font-mono-metric text-[11px] text-slate-500">
                                ID: {item.member.memberId}
                              </span>
                            </div>
                          </div>
                        </td>

                        {/* Department & Year */}
                        <td className="py-3.5 px-6">
                          <div>
                            <span className="font-semibold text-slate-800">{item.member.departmentName}</span>
                            <div className="text-[11px] text-slate-500 font-mono-metric">
                              {item.member.academicYear || "3rd Year"}
                            </div>
                          </div>
                        </td>

                        {/* Email */}
                        <td className="py-3.5 px-6">
                          <span className="font-mono-metric text-slate-600 text-xs">{item.member.email}</span>
                        </td>

                        {/* Status Chip */}
                        <td className="py-3.5 px-6">
                          <span
                            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono-metric font-semibold ${
                              isPresent
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                : isAbsent
                                ? "bg-rose-50 text-rose-700 border border-rose-200"
                                : "bg-amber-50 text-amber-700 border border-amber-200"
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                isPresent ? "bg-emerald-500" : isAbsent ? "bg-rose-500" : "bg-amber-500"
                              }`}
                            ></span>
                            {item.status}
                          </span>
                        </td>

                        {/* Quick Attendance Toggle Buttons */}
                        <td className="py-3.5 px-6 text-center">
                          <div className="inline-flex items-center p-1 rounded-xl bg-slate-100 border border-slate-200 gap-1">
                            <button
                              onClick={() => handleToggleStatus(item.member.memberId, "PRESENT")}
                              className={`px-3 py-1 rounded-lg text-xs font-semibold font-mono-metric transition-all ${
                                isPresent
                                  ? "bg-emerald-600 text-white shadow-xs font-bold"
                                  : "text-slate-600 hover:text-slate-900 hover:bg-white/60"
                              }`}
                              title="Mark Present"
                            >
                              P
                            </button>

                            <button
                              onClick={() => handleToggleStatus(item.member.memberId, "ABSENT")}
                              className={`px-3 py-1 rounded-lg text-xs font-semibold font-mono-metric transition-all ${
                                isAbsent
                                  ? "bg-rose-600 text-white shadow-xs font-bold"
                                  : "text-slate-600 hover:text-slate-900 hover:bg-white/60"
                              }`}
                              title="Mark Absent"
                            >
                              A
                            </button>

                            <button
                              onClick={() => handleToggleStatus(item.member.memberId, "LATE")}
                              className={`px-3 py-1 rounded-lg text-xs font-semibold font-mono-metric transition-all ${
                                isLate
                                  ? "bg-amber-500 text-white shadow-xs font-bold"
                                  : "text-slate-600 hover:text-slate-900 hover:bg-white/60"
                              }`}
                              title="Mark Late"
                            >
                              L
                            </button>
                          </div>
                        </td>

                        {/* Privileged President Delete Button */}
                        {role === "PRESIDENT" && (
                          <td className="py-3.5 px-6 text-right">
                            {item.attendanceId ? (
                              <button
                                onClick={() => handleDeleteAttendance(item.attendanceId, item.member.name)}
                                className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-50 hover:text-rose-700 transition-colors"
                                title="President privilege: Delete attendance record"
                              >
                                <span className="material-symbols-outlined text-lg">delete</span>
                              </button>
                            ) : (
                              <span className="text-[11px] text-slate-400 font-mono-metric">Pending</span>
                            )}
                          </td>
                        )}
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Table Footer */}
          <div className="py-4 px-6 bg-slate-50/80 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
            <span>Showing {filteredRoster.length} of {roster.length} registered members</span>
            <span>VIT Mithra Attendance Portal • Campus Edition</span>
          </div>
        </div>

        {/* Sticky Desktop Bottom Changes Bar */}
        {counts.modifiedCount > 0 && (
          <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 max-w-2xl w-full px-4 animate-fadeIn">
            <div className="p-4 rounded-2xl bg-slate-900 text-white shadow-2xl border border-slate-800 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-amber-400 text-2xl">pending_actions</span>
                <div>
                  <div className="font-bold text-sm">
                    {counts.modifiedCount} Pending Roll Modification{counts.modifiedCount > 1 ? "s" : ""}
                  </div>
                  <div className="text-xs text-slate-400">
                    Changes are staged locally. Click save to commit to Firestore.
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleDiscard}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
                >
                  Discard
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold shadow-md shadow-amber-500/20 transition-all active:scale-[0.98]"
                >
                  {saving ? "Saving..." : "Commit Changes"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Saved Sessions Modal / Slide-over */}
        {showSessionsDrawer && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
            <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden">
              {/* Modal Header */}
              <div className="p-6 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-amber-600 text-2xl">history</span>
                    <h2 className="font-headline text-lg font-bold text-slate-900">
                      Saved Attendance Sessions Log
                    </h2>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    All past club meeting sessions saved in the cloud database. Click any date to inspect and edit the roll.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowSessionsDrawer(false)}
                  className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 transition-colors"
                >
                  <span className="material-symbols-outlined text-lg">close</span>
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-6 overflow-y-auto space-y-3 flex-1">
                {savedSessions.length === 0 ? (
                  <div className="text-center py-10 text-slate-400 text-xs">
                    No saved attendance sessions found. Mark attendance and save to see sessions here.
                  </div>
                ) : (
                  savedSessions.map((session) => {
                    const isCurrent = session.date === date;
                    return (
                      <div
                        key={session.date}
                        className={`p-4 rounded-2xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                          isCurrent
                            ? "bg-amber-50/60 border-amber-300 ring-2 ring-amber-200"
                            : "bg-slate-50 hover:bg-white border-slate-200 hover:shadow-xs"
                        }`}
                      >
                        <div className="flex items-center gap-3.5">
                          <div className="w-12 h-12 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col items-center justify-center shrink-0">
                            <span className="text-[10px] uppercase font-bold text-slate-400 font-mono-metric leading-none">
                              {new Date(session.date + "T00:00:00").toLocaleString("en-US", { month: "short" })}
                            </span>
                            <span className="text-base font-extrabold text-slate-900 font-mono-metric leading-none mt-0.5">
                              {session.date.split("-")[2]}
                            </span>
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-mono-metric font-bold text-slate-900 text-sm">
                                {session.date}
                              </span>
                              {isCurrent && (
                                <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[10px] font-bold font-mono-metric">
                                  Currently Active
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                              <span className="flex items-center gap-1 text-emerald-700 font-medium">
                                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                {session.presentCount} Present
                              </span>
                              <span className="flex items-center gap-1 text-rose-700 font-medium">
                                <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                                {session.absentCount} Absent
                              </span>
                              {session.lateCount > 0 && (
                                <span className="flex items-center gap-1 text-amber-700 font-medium">
                                  <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                                  {session.lateCount} Late
                                </span>
                              )}
                              <span className="text-[11px] text-slate-400">
                                • Verified by {session.markedBy || "Admin"}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 self-end sm:self-center">
                          <div className="text-right hidden sm:block">
                            <span className="font-mono-metric font-bold text-slate-900 text-sm block">
                              {session.percentage.toFixed(1)}%
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono-metric">
                              Quorum
                            </span>
                          </div>
                          {/* Quick Export CSV & Excel for this session */}
                          <div className="flex items-center gap-1.5">
                            <button
                              type="button"
                              onClick={() => handleExport(session.date, "csv")}
                              disabled={isExporting}
                              className="px-2.5 py-2 rounded-xl bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold shadow-xs transition-colors flex items-center gap-1 disabled:opacity-60"
                              title={`Export UTF-8 BOM CSV for ${session.date} (opens in Excel & folders)`}
                            >
                              <span className="material-symbols-outlined text-base text-emerald-600">download</span>
                              <span className="hidden sm:inline">CSV</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleExport(session.date, "excel")}
                              disabled={isExporting}
                              className="px-2.5 py-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-800 text-xs font-semibold shadow-xs transition-colors flex items-center gap-1 disabled:opacity-60"
                              title={`Export formatted Excel (.xlsx) for ${session.date}`}
                            >
                              <span className="material-symbols-outlined text-base text-emerald-700">table_view</span>
                              <span className="hidden sm:inline">Excel</span>
                            </button>
                          </div>

                          <button
                            type="button"
                            onClick={() => {
                              setDate(session.date);
                              setShowSessionsDrawer(false);
                              showFeedback("Loaded Session", `Opened attendance roll for ${session.date}`, "success");
                            }}
                            className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
                              isCurrent
                                ? "bg-amber-600 text-white shadow-xs"
                                : "bg-white hover:bg-slate-100 text-slate-800 border border-slate-200 shadow-xs"
                            }`}
                          >
                            <span>{isCurrent ? "Currently Loaded" : "Inspect & Edit"}</span>
                            <span className="material-symbols-outlined text-sm">arrow_forward</span>
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Modal Footer */}
              <div className="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
                <span>{savedSessions.length} recorded session(s) in system</span>
                <button
                  type="button"
                  onClick={() => setShowSessionsDrawer(false)}
                  className="px-4 py-1.5 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-800 font-semibold transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
