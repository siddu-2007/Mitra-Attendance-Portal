"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { Member, StudentAttendanceData, StudentTeamData } from "@/lib/types";
import { useAuth } from "@/lib/auth-context";

export default function StudentPortalPage() {
  const router = useRouter();
  const { role, student, admin, isAuthenticated, isLoading } = useAuth();
  const [profile, setProfile] = useState<Member | null>(student);
  const [attendance, setAttendance] = useState<StudentAttendanceData | null>(null);
  const [team, setTeam] = useState<StudentTeamData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState<"attendance" | "team">("attendance");

  useEffect(() => {
    async function loadStudentData() {
      setLoading(true);
      try {
        // 1. Fetch student profile
        try {
          const profRes = await api.getStudentMe();
          if (profRes.data) {
            setProfile(profRes.data);
          }
        } catch (e) {
          console.warn("Using contextual student profile");
        }

        // 2. Fetch attendance history
        try {
          const attRes = await api.getStudentAttendance();
          if (attRes.data) {
            setAttendance(attRes.data);
          }
        } catch (e) {
          console.warn("Using fallback student attendance");
          setAttendance({
            memberId: student?.memberId || "Student",
            memberName: student?.name || "Student Member",
            departmentId: student?.departmentId || "ai",
            departmentName: student?.departmentName || "Club Wing",
            overallAttendancePercentage: 100.0,
            totalSessions: 0,
            presentCount: 0,
            absentCount: 0,
            lateCount: 0,
            history: [],
          });
        }

        // 3. Fetch department team
        try {
          const teamRes = await api.getStudentTeam();
          if (teamRes.data) {
            setTeam(teamRes.data);
          }
        } catch (e) {
          console.warn("Using fallback team data");
          setTeam({
            departmentId: student?.departmentId || "ai",
            departmentName: student?.departmentName || "Club Wing",
            totalMembers: 1,
            teamMembers: student ? [{ ...student, isMe: true }] : [],
          });
        }
      } finally {
        setLoading(false);
      }
    }

    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    loadStudentData();
  }, [student, role, isAuthenticated, isLoading, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen bg-[#F8FAFC]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-3 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs font-semibold text-slate-500 tracking-wide font-mono-metric">
            Loading Student Portal...
          </p>
        </div>
      </div>
    );
  }

  const percentage = attendance?.overallAttendancePercentage ?? 100;
  const isGoodStanding = percentage >= 75;

  // Radial calculation: circumference = 2 * Math.PI * 44 ~= 276.46
  const circumference = 276.46;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="bg-[#F8FAFC] font-sans text-[#0F172A] flex flex-col min-h-screen">
      <Header />

      <main className="flex-1 w-full pt-20 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {/* Top Profile Welcome Banner */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-[0_1px_3px_rgba(0,0,0,0.03)] mb-8 relative overflow-hidden">
          <div className="absolute -top-12 -right-12 w-64 h-64 bg-amber-400/10 rounded-full blur-3xl pointer-events-none"></div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
            {/* Student Info */}
            <div className="flex items-center gap-4 sm:gap-5">
              <div className="w-16 h-16 rounded-2xl bg-slate-900 text-amber-400 font-headline font-bold text-2xl flex items-center justify-center shadow-md shadow-slate-900/10 shrink-0">
                {profile?.name?.charAt(0) || "S"}
              </div>

              <div>
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <h1 className="font-headline text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
                    {profile?.name || "Student Member"}
                  </h1>
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono-metric font-bold bg-amber-100 text-amber-900 border border-amber-300">
                    Roll: {profile?.memberId || "Registration Number"}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono-metric font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Active Member
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-500 font-medium">
                  <span className="flex items-center gap-1.5 text-slate-700 font-semibold">
                    <span className="material-symbols-outlined text-amber-600 text-base">domain</span>
                    <span>{profile?.departmentName || attendance?.departmentName || "Assigned Wing"}</span>
                  </span>
                  <span>•</span>
                  <span>{profile?.academicYear || "Club Member"}</span>
                  <span>•</span>
                  <span className="font-mono-metric">{profile?.email || (profile?.memberId ? `${profile.memberId.toLowerCase()}@vitstudent.ac.in` : "student@vitstudent.ac.in")}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Navigation Tabs (Attendance Roll vs Team Roster) */}
          <div className="flex items-center gap-2 mt-6 pt-6 border-t border-slate-100">
            <button
              onClick={() => setActiveView("attendance")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeView === "attendance"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <span className="material-symbols-outlined text-base">how_to_reg</span>
              <span>My Attendance History</span>
            </button>

            <button
              onClick={() => setActiveView("team")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeView === "team"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <span className="material-symbols-outlined text-base">groups</span>
              <span>My Department &amp; Team ({team?.totalMembers || 2})</span>
            </button>
          </div>
        </div>

        {/* View 1: Personal Attendance History */}
        {activeView === "attendance" && (
          <div className="space-y-8">
            {/* KPI Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              {/* Overall Percentage Card */}
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Attendance Rate</span>
                  <div className="flex items-baseline gap-1 mt-2">
                    <span className="font-mono-metric text-3xl font-bold text-slate-900">
                      {percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-[11px] text-emerald-600 font-medium mt-1 font-mono-metric">
                    Min 75% required
                  </div>
                </div>

                {/* Donut Mini SVG */}
                <div className="relative w-16 h-16 flex items-center justify-center">
                  <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" fill="none" r="44" stroke="#f1f5f9" strokeWidth="10" />
                    <circle
                      cx="50"
                      cy="50"
                      fill="none"
                      r="44"
                      stroke={isGoodStanding ? "#10b981" : "#f43f5e"}
                      strokeDasharray="276.46"
                      strokeDashoffset={strokeDashoffset}
                      strokeLinecap="round"
                      strokeWidth="10"
                    />
                  </svg>
                  <span className="absolute font-mono-metric text-[11px] font-bold text-slate-800">
                    {Math.round(percentage)}%
                  </span>
                </div>
              </div>

              {/* Sessions Attended */}
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Sessions Attended</span>
                  <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <span className="material-symbols-outlined text-lg">check_circle</span>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="font-mono-metric text-3xl font-bold text-emerald-600">
                    {attendance?.presentCount ?? 5}
                  </div>
                  <div className="text-xs text-slate-500 font-mono-metric mt-1">
                    Marked Present on roll
                  </div>
                </div>
              </div>

              {/* Sessions Missed */}
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Sessions Missed</span>
                  <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
                    <span className="material-symbols-outlined text-lg">cancel</span>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="font-mono-metric text-3xl font-bold text-rose-600">
                    {attendance?.absentCount ?? 0}
                  </div>
                  <div className="text-xs text-slate-500 font-mono-metric mt-1">
                    Unexcused absences
                  </div>
                </div>
              </div>

              {/* Total Logged Sessions */}
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Club Meets</span>
                  <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                    <span className="material-symbols-outlined text-lg">calendar_today</span>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="font-mono-metric text-3xl font-bold text-slate-900">
                    {attendance?.totalSessions ?? 5}
                  </div>
                  <div className="text-xs text-slate-500 font-mono-metric mt-1">
                    Official sessions conducted
                  </div>
                </div>
              </div>
            </div>

            {/* Attendance History Table */}
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] overflow-hidden">
              <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="font-headline text-base font-bold text-slate-900">
                    Session-by-Session Attendance Roll
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Chronological verification log recorded by club administrators.
                  </p>
                </div>
                <span className="text-xs font-mono-metric text-slate-500 px-3 py-1 rounded-full bg-slate-100">
                  {attendance?.history?.length ?? 0} Record(s) Found
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-mono-metric font-semibold text-slate-500 uppercase tracking-wider">
                      <th className="py-3.5 px-6">Meeting Date</th>
                      <th className="py-3.5 px-6">Attendance Status</th>
                      <th className="py-3.5 px-6">Verified By</th>
                      <th className="py-3.5 px-6">Department Wing</th>
                      <th className="py-3.5 px-6 text-right">System Verification</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-xs">
                    {loading ? (
                      <tr>
                        <td colSpan={5} className="py-12 text-center text-slate-500">
                          <div className="flex items-center justify-center gap-2">
                            <span className="material-symbols-outlined animate-spin text-amber-500">progress_activity</span>
                            <span>Retrieving attendance history...</span>
                          </div>
                        </td>
                      </tr>
                    ) : !attendance || attendance.history.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-12 text-center text-slate-500">
                          No attendance records logged for your roll number yet.
                        </td>
                      </tr>
                    ) : (
                      attendance.history.map((record, index) => {
                        const isPres = record.status === "PRESENT";
                        const isAbs = record.status === "ABSENT";

                        return (
                          <tr key={record.attendanceId || index} className="hover:bg-slate-50/80 transition-colors">
                            {/* Date */}
                            <td className="py-3.5 px-6">
                              <div className="flex items-center gap-2 font-mono-metric font-semibold text-slate-800">
                                <span className="material-symbols-outlined text-slate-400 text-base">event</span>
                                <span>{record.date}</span>
                              </div>
                            </td>

                            {/* Status Chip */}
                            <td className="py-3.5 px-6">
                              <span
                                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono-metric font-bold ${
                                  isPres
                                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                    : isAbs
                                    ? "bg-rose-50 text-rose-700 border border-rose-200"
                                    : "bg-amber-50 text-amber-700 border border-amber-200"
                                }`}
                              >
                                <span
                                  className={`w-1.5 h-1.5 rounded-full ${
                                    isPres ? "bg-emerald-500" : isAbs ? "bg-rose-500" : "bg-amber-500"
                                  }`}
                                ></span>
                                {record.status}
                              </span>
                            </td>

                            {/* Verified By */}
                            <td className="py-3.5 px-6">
                              <span className="text-slate-600 font-medium">
                                {record.markedBy || "Operations Admin"}
                              </span>
                            </td>

                            {/* Department */}
                            <td className="py-3.5 px-6">
                              <span className="text-slate-600 font-mono-metric">
                                {attendance?.departmentName || profile?.departmentName || "Assigned Wing"}
                              </span>
                            </td>

                            {/* Verification timestamp */}
                            <td className="py-3.5 px-6 text-right">
                              <span className="text-[11px] font-mono-metric text-slate-400">
                                Logged • Firestore
                              </span>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* View 2: My Department & Team */}
        {activeView === "team" && (
          <div className="space-y-8">
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                <div>
                  <span className="text-xs font-mono-metric uppercase text-amber-600 font-bold tracking-wider">
                    Wing Roster &amp; Colleagues
                  </span>
                  <h2 className="font-headline text-xl font-bold text-slate-900 mt-0.5">
                    {team?.departmentName || profile?.departmentName || "Department Wing"}
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Connect with fellow student club members enrolled in your specialized department.
                  </p>
                </div>
                <div className="px-3 py-1.5 rounded-xl bg-slate-100 border border-slate-200 text-xs font-mono-metric font-semibold text-slate-700">
                  {team?.totalMembers || 0} Registered Members
                </div>
              </div>

              {/* Team Members Table */}
              <div className="overflow-x-auto rounded-xl border border-slate-200/80">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-mono-metric font-semibold text-slate-500 uppercase tracking-wider">
                      <th className="py-3.5 px-6">Teammate Profile</th>
                      <th className="py-3.5 px-6">Roll Number / ID</th>
                      <th className="py-3.5 px-6">Academic Year</th>
                      <th className="py-3.5 px-6">Campus Email</th>
                      <th className="py-3.5 px-6 text-right">Role</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-xs">
                    {team?.teamMembers?.map((member) => (
                      <tr
                        key={member.memberId}
                        className={`hover:bg-slate-50/80 transition-colors ${
                          member.isMe ? "bg-amber-50/40" : ""
                        }`}
                      >
                        {/* Member */}
                        <td className="py-3.5 px-6">
                          <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-xl bg-slate-900 text-amber-400 font-bold flex items-center justify-center text-xs shrink-0">
                              {member.name.charAt(0)}
                            </div>
                            <div>
                              <div className="font-headline font-bold text-slate-900 flex items-center gap-2">
                                <span>{member.name}</span>
                                {member.isMe && (
                                  <span className="text-[10px] bg-amber-200/80 text-amber-900 font-mono-metric font-bold px-2 py-0.5 rounded-full">
                                    YOU
                                  </span>
                                )}
                              </div>
                              <span className="text-[11px] text-slate-500">{team.departmentName}</span>
                            </div>
                          </div>
                        </td>

                        {/* Roll Number */}
                        <td className="py-3.5 px-6">
                          <span className="font-mono-metric font-bold text-slate-700">{member.memberId}</span>
                        </td>

                        {/* Academic Year */}
                        <td className="py-3.5 px-6">
                          <span className="text-slate-600 font-medium">{member.academicYear}</span>
                        </td>

                        {/* Email */}
                        <td className="py-3.5 px-6">
                          <span className="font-mono-metric text-slate-600">{member.email}</span>
                        </td>

                        {/* Role Status */}
                        <td className="py-3.5 px-6 text-right">
                          <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-mono-metric text-[11px] font-semibold">
                            Active Member
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Informative Footer Notice */}
        <div className="mt-8 p-4 rounded-2xl bg-amber-50/60 border border-amber-200/60 text-xs text-amber-900 flex items-start gap-3">
          <span className="material-symbols-outlined text-amber-700 text-xl shrink-0 mt-0.5">info</span>
          <div>
            <span className="font-bold">Attendance Policy Notice:</span> Daily attendance rolls are marked and locked by
            authorized Club Administrators. If you have questions regarding an unexcused absence or require On-Duty (OD)
            clearance for university events, please contact your Department Lead or Club President.
          </div>
        </div>
      </main>
    </div>
  );
}
