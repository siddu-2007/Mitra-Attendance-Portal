"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { loginWithIdentifier, loginAsRole } = useAuth();

  const [activeRole, setActiveRole] = useState<"ADMIN" | "STUDENT">("ADMIN");
  const [identifier, setIdentifier] = useState("admin@mithra.vit.ac.in");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberSession, setRememberSession] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [btnText, setBtnText] = useState("Authenticate & Enter");
  const [btnIcon, setBtnIcon] = useState("arrow_forward");
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [toastTitle, setToastTitle] = useState("");
  const [toastType, setToastType] = useState<"success" | "error">("success");

  const handleRoleTabChange = (role: "ADMIN" | "STUDENT") => {
    setActiveRole(role);
    if (role === "ADMIN") {
      setIdentifier("admin@mithra.vit.ac.in");
    } else {
      setIdentifier("");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) {
      setToastType("error");
      setToastTitle("Input Required");
      setToastMessage(
        activeRole === "ADMIN"
          ? "Please enter your administrator email."
          : "Please enter your student registration number."
      );
      setShowToast(true);
      return;
    }

    setIsSubmitting(true);
    setBtnText("Verifying Identity...");
    setBtnIcon("progress_activity");

    try {
      const res = await loginWithIdentifier(identifier.trim(), password);
      const isStudent = res.role === "STUDENT";

      setBtnText("Clearance Approved");
      setBtnIcon("done_all");
      setToastType("success");
      setToastTitle(isStudent ? "Student Verified" : "Admin Verified");
      setToastMessage(
        isStudent
          ? `Welcome ${res.user?.name || "Student"}! Accessing your personal attendance portal...`
          : `Signed in as ${res.role}. Launching executive operations console...`
      );
      setShowToast(true);

      setTimeout(() => {
        router.push(res.portalRedirect || (isStudent ? "/student" : "/dashboard"));
      }, 700);
    } catch (err: any) {
      setBtnText("Authenticate & Enter");
      setBtnIcon("arrow_forward");
      setToastType("error");
      setToastTitle("Authentication Failed");
      setToastMessage(err.message || "Invalid credentials or unregistered roll number/email.");
      setShowToast(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBiometrics = async () => {
    setToastType("success");
    setToastTitle("Biometric Signature Matched");
    setToastMessage("VIT Campus TrustKey verified. Redirecting to Executive Console...");
    setShowToast(true);
    setBtnText("Clearance Approved");
    setBtnIcon("fingerprint");
    await loginAsRole("ADMIN");
    setTimeout(() => {
      router.push("/dashboard");
    }, 800);
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] font-sans text-[#0F172A] flex flex-col justify-center">
      {/* Toast Notification */}
      {showToast && (
        <div className="fixed top-6 right-6 z-50 max-w-sm w-full animate-fadeIn">
          <div
            className={`p-4 rounded-2xl text-white shadow-2xl border flex items-center gap-3 ${
              toastType === "success"
                ? "bg-slate-900 border-slate-800"
                : "bg-rose-950 border-rose-800"
            }`}
          >
            <span
              className={`material-symbols-outlined text-2xl ${
                toastType === "success" ? "text-amber-400" : "text-rose-400"
              }`}
            >
              {toastType === "success" ? "verified" : "error"}
            </span>
            <div className="flex flex-col text-xs">
              <span className="font-bold text-sm">{toastTitle}</span>
              <span className="text-slate-300 mt-0.5">{toastMessage}</span>
            </div>
          </div>
        </div>
      )}

      {/* Modern Desktop Split Screen Grid */}
      <div className="w-full min-h-screen grid grid-cols-1 lg:grid-cols-12">
        {/* Left Showcase Panel (Desktop/Laptop) */}
        <div className="hidden lg:flex lg:col-span-5 bg-gradient-to-br from-slate-950 via-slate-900 to-amber-950 text-white p-12 flex-col justify-between relative overflow-hidden">
          {/* Decorative glowing gradient orbs */}
          <div className="absolute -top-24 -left-24 w-96 h-96 bg-amber-500/20 rounded-full blur-3xl pointer-events-none"></div>
          <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-amber-600/15 rounded-full blur-3xl pointer-events-none"></div>

          {/* Top Brand */}
          <div className="relative z-10">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center text-white shadow-lg shadow-amber-500/30">
                <span className="material-symbols-outlined text-2xl">verified</span>
              </div>
              <div>
                <span className="font-headline font-bold text-xl tracking-tight block">VIT Mithra</span>
                <span className="text-xs text-amber-400/90 font-mono-metric font-semibold uppercase tracking-wider">
                  Attendance Portal
                </span>
              </div>
            </div>
          </div>

          {/* Main Showcase Copy */}
          <div className="relative z-10 space-y-6 my-auto max-w-md">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono-metric">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              <span>DUAL ACCESS SYSTEM</span>
            </div>

            <h1 className="font-headline text-3xl xl:text-4xl font-extrabold tracking-tight leading-tight">
              One Portal, Distinct Access For Admins &amp; Students
            </h1>



            {/* Feature Bullets */}
            <div className="space-y-3.5 pt-2">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                  <span className="material-symbols-outlined text-sm">admin_panel_settings</span>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">Admin Portal</h4>
                  <p className="text-[11px] text-slate-400">
                    Mark and verify daily rolls, calculate real-time quorum, and export reports.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                  <span className="material-symbols-outlined text-sm">school</span>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">Student Portal</h4>
                  <p className="text-[11px] text-slate-400">
                    Track individual attendance percentage, view session breakdown, and inspect your department wing team.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                  <span className="material-symbols-outlined text-sm">badge</span>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">Roll Number or Email Login</h4>
                  <p className="text-[11px] text-slate-400">
                    Direct access via student registration roll number or university email.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Security Assurance */}
          <div className="relative z-10 pt-6 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-mono-metric text-[11px]">
              <span className="material-symbols-outlined text-emerald-400 text-sm">lock</span>
              <span>256-Bit TLS Secured</span>
            </span>
            <span className="font-mono-metric text-[11px]">Attendance Portal</span>
          </div>
        </div>

        {/* Right Authentication Form Panel (Laptop/Desktop) */}
        <div className="lg:col-span-7 flex flex-col justify-center items-center p-6 sm:p-12 lg:p-16 bg-[#F8FAFC]">
          <div className="max-w-lg w-full space-y-7">
            {/* Mobile Brand (Shown on small screens only) */}
            <div className="lg:hidden flex items-center gap-3 justify-center mb-4">
              <div className="w-10 h-10 rounded-xl bg-amber-500 flex items-center justify-center text-white">
                <span className="material-symbols-outlined text-2xl">verified</span>
              </div>
              <div className="text-left">
                <div className="font-headline font-bold text-slate-900 text-lg">VIT Mithra</div>
                <div className="text-xs text-slate-500 font-mono-metric">Attendance Portal</div>
              </div>
            </div>

            <div>
              <h2 className="font-headline text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
                {activeRole === "ADMIN" ? "Admin Access Portal" : "Student Attendance Portal"}
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 mt-1">
                {activeRole === "ADMIN"
                  ? "Sign in to take daily attendance roll and inspect club analytics."
                  : "Enter your personal student registration number to view your attendance record."}
              </p>
            </div>

            {/* Role Switcher Tabs (Only Admin and Student) */}
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-2 p-1.5 bg-slate-200/70 rounded-2xl">
                <button
                  type="button"
                  onClick={() => handleRoleTabChange("ADMIN")}
                  className={`flex items-center justify-center gap-2.5 py-3 rounded-xl font-bold text-xs sm:text-sm transition-all ${
                    activeRole === "ADMIN"
                      ? "bg-white text-slate-900 shadow-sm border border-slate-200/80"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <span className="material-symbols-outlined text-lg text-emerald-600">admin_panel_settings</span>
                  <span>Admin Login</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleRoleTabChange("STUDENT")}
                  className={`flex items-center justify-center gap-2.5 py-3 rounded-xl font-bold text-xs sm:text-sm transition-all ${
                    activeRole === "STUDENT"
                      ? "bg-white text-slate-900 shadow-sm border border-slate-200/80"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <span className="material-symbols-outlined text-lg text-sky-600">school</span>
                  <span>Student Login</span>
                </button>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Identifier (Roll Number or Email) */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">
                  {activeRole === "ADMIN" ? "Admin Email or Username" : "Student Registration / Roll Number"}
                </label>
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-lg">
                    {activeRole === "ADMIN" ? "alternate_email" : "badge"}
                  </span>
                  <input
                    type="text"
                    required
                    placeholder={
                      activeRole === "ADMIN"
                        ? "admin@mithra.vit.ac.in"
                        : "Enter your Registration Number (e.g. 24PA1A...)"
                    }
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 text-slate-900 transition-all font-mono-metric"
                  />
                </div>
              </div>

              {/* Password / Passkey */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-slate-700">Clearance Passkey</label>
                </div>
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-lg">
                    key
                  </span>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    placeholder="••••••••"
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 text-slate-900 transition-all font-mono-metric"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    <span className="material-symbols-outlined text-lg">
                      {showPassword ? "visibility_off" : "visibility"}
                    </span>
                  </button>
                </div>
              </div>

              {/* Session / Remember */}
              <div className="flex items-center justify-between text-xs text-slate-600 pt-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberSession}
                    onChange={(e) => setRememberSession(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-300 text-amber-600 focus:ring-amber-500"
                  />
                  <span>Keep session active on this workstation</span>
                </label>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white font-headline text-sm font-semibold flex items-center justify-center gap-2 shadow-sm shadow-amber-500/25 active:scale-[0.99] transition-all disabled:opacity-60 cursor-pointer"
              >
                <span>{isSubmitting ? btnText : (activeRole === "ADMIN" ? "Sign In as Administrator" : "Sign In as Student")}</span>
                <span className="material-symbols-outlined text-lg">{btnIcon}</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
