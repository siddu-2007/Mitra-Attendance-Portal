"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { admin, student, role, logout } = useAuth();
  const [showRoleMenu, setShowRoleMenu] = useState(false);

  const isStudent = role === "STUDENT";

  const navLinks = isStudent
    ? [
        { name: "My Attendance & Team", href: "/student", icon: "how_to_reg" },
      ]
    : [
        { name: "Executive Dashboard", href: "/dashboard", icon: "dashboard" },
        { name: "Daily Attendance Roll", href: "/attendance", icon: "how_to_reg" },
      ];

  const homeHref = isStudent ? "/student" : "/dashboard";

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-xl border-b border-slate-200 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="h-16 flex items-center justify-between">
          {/* Brand & Club Identity */}
          <div className="flex items-center gap-8">
            <Link href={homeHref} className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 border border-amber-600/30 flex items-center justify-center text-white shadow-sm shadow-amber-500/20 group-hover:scale-105 transition-transform">
                <span className="material-symbols-outlined text-2xl">verified</span>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-headline text-lg font-bold text-slate-900 tracking-tight leading-none">
                    VIT Mithra
                  </span>
                  <span
                    className={`text-[10px] uppercase font-mono-metric font-bold px-2 py-0.5 rounded-full border ${
                      role === "PRESIDENT"
                        ? "bg-amber-100 text-amber-900 border-amber-300"
                        : role === "ADMIN"
                        ? "bg-emerald-100 text-emerald-900 border-emerald-300"
                        : role === "STUDENT"
                        ? "bg-sky-100 text-sky-900 border-sky-300"
                        : "bg-rose-100 text-rose-900 border-rose-300"
                    }`}
                  >
                    {isStudent ? `Student (${student?.memberId || "Member"})` : role || "Admin"}
                  </span>
                </div>
                <span className="text-xs text-slate-500 leading-tight font-medium">
                  {isStudent ? "Student Member Attendance & Team Portal" : "Executive Attendance & Quorum Console"}
                </span>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <nav className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? "bg-amber-500/10 text-amber-700 font-semibold shadow-xs"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                    }`}
                  >
                    <span
                      className={`material-symbols-outlined text-lg ${
                        isActive ? "text-amber-600" : "text-slate-400"
                      }`}
                    >
                      {link.icon}
                    </span>
                    <span>{link.name}</span>
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Right Header Operations & Profile */}
          <div className="flex items-center gap-3">
            {/* Live Backend Connection Indicator */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100/90 border border-slate-200 text-xs font-mono-metric text-slate-600">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="font-medium text-slate-700">System Online</span>
            </div>

            {/* Role Clearance Selector & Profile Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowRoleMenu(!showRoleMenu)}
                className="flex items-center gap-2.5 p-1.5 sm:px-3 sm:py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 shadow-xs text-xs font-semibold text-slate-700 transition-all active:scale-[0.98]"
              >
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
                    isStudent
                      ? "bg-sky-700 text-sky-100"
                      : "bg-slate-900 text-amber-400"
                  }`}
                >
                  {isStudent ? student?.name?.charAt(0) || "S" : admin?.name?.charAt(0) || "A"}
                </div>
                <div className="hidden lg:flex flex-col text-left">
                  <span className="font-semibold text-slate-900 text-xs leading-tight">
                    {isStudent ? student?.name || "Student" : admin?.name || "Administrator"}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono-metric leading-tight font-normal">
                    {role === "PRESIDENT"
                      ? "President"
                      : role === "ADMIN"
                      ? "Operations Admin"
                      : `Roll: ${student?.memberId || ""}`}
                  </span>
                </div>
                <span className="material-symbols-outlined text-slate-400 text-sm">unfold_more</span>
              </button>

              {/* User Menu Dropdown */}
              {showRoleMenu && (
                <div className="absolute right-0 mt-2 w-72 bg-white rounded-2xl shadow-xl border border-slate-200 py-2 z-50 animate-fadeIn text-left text-xs">
                  <div className="px-4 py-2 border-b border-slate-100">
                    <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Current Identity
                    </p>
                    <p className="text-xs font-bold text-slate-800 mt-0.5">
                      {role === "STUDENT" ? student?.name || "Student Member" : admin?.name || "Operations Admin"}
                    </p>
                    <p className="text-[11px] text-slate-500 font-mono-metric">
                      {role === "STUDENT" ? `Roll: ${student?.memberId || ""}` : admin?.email || "admin@mithra.vit.ac.in"}
                    </p>
                  </div>

                  <div className="p-1 space-y-0.5">
                    {role !== "STUDENT" ? (
                      <>
                        <Link
                          href="/dashboard"
                          onClick={() => setShowRoleMenu(false)}
                          className="w-full px-3 py-2 rounded-xl text-left hover:bg-slate-50 flex items-center gap-2 text-slate-700 font-medium"
                        >
                          <span className="material-symbols-outlined text-base text-amber-600">dashboard</span>
                          <span>Executive Dashboard</span>
                        </Link>
                        <Link
                          href="/attendance"
                          onClick={() => setShowRoleMenu(false)}
                          className="w-full px-3 py-2 rounded-xl text-left hover:bg-slate-50 flex items-center gap-2 text-slate-700 font-medium"
                        >
                          <span className="material-symbols-outlined text-base text-emerald-600">how_to_reg</span>
                          <span>Daily Attendance Roll</span>
                        </Link>
                      </>
                    ) : (
                      <Link
                        href="/student"
                        onClick={() => setShowRoleMenu(false)}
                        className="w-full px-3 py-2 rounded-xl text-left hover:bg-slate-50 flex items-center gap-2 text-slate-700 font-medium"
                      >
                        <span className="material-symbols-outlined text-base text-sky-600">school</span>
                        <span>My Attendance Portal</span>
                      </Link>
                    )}
                  </div>

                  <div className="border-t border-slate-100 mt-1 pt-1 px-1">
                    <button
                      onClick={() => {
                        setShowRoleMenu(false);
                        logout();
                        router.push("/login");
                      }}
                      className="w-full px-3 py-2 rounded-xl text-left hover:bg-rose-50 flex items-center gap-2 text-rose-600 font-semibold cursor-pointer transition-colors"
                    >
                      <span className="material-symbols-outlined text-base">logout</span>
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
