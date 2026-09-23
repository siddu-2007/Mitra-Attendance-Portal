"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard");
  }, [router]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-screen bg-[#F8FAFC]">
      <div className="flex flex-col items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 shadow-xs animate-pulse">
          <span className="material-symbols-outlined text-3xl">verified</span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 text-sm font-medium">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping"></span>
          <span>Connecting to VIT Mithra Portal...</span>
        </div>
      </div>
    </div>
  );
}
