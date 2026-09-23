"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { AdminProfile, AdminRole, LoginResult, Member } from "./types";
import { api } from "./api";

interface AuthContextType {
  token: string | null;
  admin: AdminProfile | null;
  student: Member | null;
  role: AdminRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginAsRole: (targetRole: AdminRole, studentId?: string) => Promise<void>;
  loginWithIdentifier: (identifier: string, passkey?: string) => Promise<LoginResult>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [admin, setAdmin] = useState<AdminProfile | null>(null);
  const [student, setStudent] = useState<Member | null>(null);
  const [role, setRole] = useState<AdminRole | null>("ADMIN");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check localStorage for saved session
    const savedToken = localStorage.getItem("mithra_auth_token");
    const savedRole = localStorage.getItem("mithra_user_role") as AdminRole | null;
    const savedAdmin = localStorage.getItem("mithra_admin_profile");
    const savedStudent = localStorage.getItem("mithra_student_profile");

    if (savedToken && savedRole) {
      setToken(savedToken);
      setRole(savedRole);
      if (savedRole === "STUDENT" && savedStudent) {
        try {
          setStudent(JSON.parse(savedStudent));
        } catch (e) {
          console.warn("Could not parse saved student profile");
        }
      } else if (savedAdmin) {
        try {
          setAdmin(JSON.parse(savedAdmin));
        } catch (e) {
          console.warn("Could not parse saved admin profile");
        }
      }
    } else {
      // Default to Admin role for initial visit
      loginAsRole("ADMIN");
    }
    setIsLoading(false);
  }, []);

  const loginWithIdentifier = async (identifier: string, passkey?: string): Promise<LoginResult> => {
    setIsLoading(true);
    try {
      const res = await api.login(identifier, passkey);
      const data = res.data;

      setToken(data.token);
      setRole(data.role as AdminRole);
      localStorage.setItem("mithra_auth_token", data.token);
      localStorage.setItem("mithra_user_role", data.role);

      if (data.role === "STUDENT") {
        const studentProfile = data.user as Member;
        setStudent(studentProfile);
        setAdmin(null);
        localStorage.setItem("mithra_student_profile", JSON.stringify(studentProfile));
        localStorage.removeItem("mithra_admin_profile");
      } else {
        const adminProfile = data.user as AdminProfile;
        setAdmin(adminProfile);
        setStudent(null);
        localStorage.setItem("mithra_admin_profile", JSON.stringify(adminProfile));
        localStorage.removeItem("mithra_student_profile");
      }

      return data;
    } finally {
      setIsLoading(false);
    }
  };

  const loginAsRole = async (targetRole: AdminRole, studentId?: string) => {
    setIsLoading(true);
    try {
      if (targetRole === "STUDENT") {
        await loginWithIdentifier(studentId || "24PA1A4511");
      } else if (targetRole === "PRESIDENT") {
        await loginWithIdentifier("president@mithra.vit.ac.in");
      } else if (targetRole === "ADMIN") {
        await loginWithIdentifier("admin@mithra.vit.ac.in");
      } else {
        // Mock unauthorized student
        const mockToken = "mock-token:unauthorized_user:guest@vitstudent.ac.in:UNAUTHORIZED:Guest";
        setToken(mockToken);
        setRole("UNAUTHORIZED");
        setAdmin(null);
        setStudent(null);
        localStorage.setItem("mithra_auth_token", mockToken);
        localStorage.setItem("mithra_user_role", "UNAUTHORIZED");
      }
    } catch (err) {
      console.warn("Could not login via API, using fallback context:", err);
      if (targetRole === "STUDENT") {
        const sid = studentId || "24PA1A4511";
        const fallbackStudent: Member = {
          memberId: sid,
          name: sid === "24PA1A4520" ? "B Mythili" : "A Sai Kiran",
          email: `${sid.toLowerCase()}@vitstudent.ac.in`,
          departmentId: sid === "24PA1A4520" ? "dept_mk" : "dept_ai",
          departmentName: sid === "24PA1A4520" ? "Marketing Team" : "Artificial Intelligence",
          academicYear: "3rd Year",
          joiningDate: "2024-08-01",
          status: "ACTIVE",
        };
        const mockToken = `mock-token:${fallbackStudent.memberId}:${fallbackStudent.email}:STUDENT:${fallbackStudent.name}`;
        setToken(mockToken);
        setRole("STUDENT");
        setStudent(fallbackStudent);
        setAdmin(null);
        localStorage.setItem("mithra_auth_token", mockToken);
        localStorage.setItem("mithra_user_role", "STUDENT");
        localStorage.setItem("mithra_student_profile", JSON.stringify(fallbackStudent));
      } else if (targetRole === "PRESIDENT" || targetRole === "ADMIN") {
        const uid = targetRole === "PRESIDENT" ? "president_01" : "admin_01";
        const email = targetRole === "PRESIDENT" ? "president@mithra.vit.ac.in" : "admin@mithra.vit.ac.in";
        const name = targetRole === "PRESIDENT" ? "Club President" : "Operations Admin";
        const fallbackAdmin: AdminProfile = {
          uid,
          name,
          email,
          role: targetRole,
          status: "ACTIVE",
          permissions: targetRole === "PRESIDENT" ? ["all"] : ["mark_attendance", "view_reports"],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        const mockToken = `mock-token:${uid}:${email}:${targetRole}:${name}`;
        setToken(mockToken);
        setRole(targetRole);
        setAdmin(fallbackAdmin);
        setStudent(null);
        localStorage.setItem("mithra_auth_token", mockToken);
        localStorage.setItem("mithra_user_role", targetRole);
        localStorage.setItem("mithra_admin_profile", JSON.stringify(fallbackAdmin));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setAdmin(null);
    setStudent(null);
    setRole(null);
    localStorage.removeItem("mithra_auth_token");
    localStorage.removeItem("mithra_user_role");
    localStorage.removeItem("mithra_admin_profile");
    localStorage.removeItem("mithra_student_profile");
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        admin,
        student,
        role,
        isAuthenticated: !!token,
        isLoading,
        loginAsRole,
        loginWithIdentifier,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
