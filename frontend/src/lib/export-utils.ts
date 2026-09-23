/**
 * Client-side file download and export utility.
 * Specifically configured for Windows Microsoft Excel & folder compatibility.
 */

import { api } from "./api";

/**
 * Triggers a browser file download safely across all browsers and operating systems.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.style.display = "none";
  a.href = url;
  a.setAttribute("download", filename);

  // Append to document body before triggering click (required for Firefox/Edge/Chrome on Windows)
  document.body.appendChild(a);
  a.click();

  // Defer removal so the browser's download manager can properly register the file stream
  setTimeout(() => {
    if (document.body.contains(a)) {
      document.body.removeChild(a);
    }
    window.URL.revokeObjectURL(url);
  }, 1500);
}

/**
 * Generates a client-side CSV with UTF-8 BOM from the active roster.
 * This guarantees that even if offline or if backend export encounters network errors,
 * the admin can ALWAYS download a valid CSV that opens cleanly in Excel and folders.
 */
export function generateClientCSV(date: string, roster: Array<{ member: any; status: string }>): Blob {
  const headers = ["Attendance ID", "Date", "Member ID", "Member Name", "Department", "Academic Year", "Status", "Marked By"];
  
  const escapeCSV = (val: any) => {
    const s = String(val ?? "").replace(/"/g, '""');
    return `"${s}"`;
  };

  const rows = roster.map((item) => [
    escapeCSV(`${item.member.memberId}_${date}`),
    escapeCSV(date),
    escapeCSV(item.member.memberId),
    escapeCSV(item.member.name),
    escapeCSV(item.member.departmentName || "General"),
    escapeCSV(item.member.academicYear || "3rd Year"),
    escapeCSV(item.status),
    escapeCSV("Operations Admin"),
  ]);

  const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\r\n");

  // Include UTF-8 BOM (\uFEFF) at the start so Microsoft Excel on Windows parses encoding properly
  return new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
}

/**
 * Downloads attendance report in CSV or Excel format.
 */
export async function downloadAttendanceReport(
  date: string,
  format: "csv" | "excel" = "csv",
  fallbackRoster?: Array<{ member: any; status: string }>
): Promise<void> {
  const extension = format === "excel" ? "xlsx" : "csv";
  const cleanDate = date || new Date().toISOString().split("T")[0];
  const filename = `Mithra_Attendance_${cleanDate}.${extension}`;

  try {
    const blob = await api.exportAttendanceReport(format, cleanDate);
    
    if (format === "csv") {
      // Ensure UTF-8 BOM is present for Excel on Windows
      const text = await blob.text();
      const hasBOM = text.charCodeAt(0) === 0xFEFF;
      const finalBlob = hasBOM
        ? blob
        : new Blob(["\uFEFF" + text], { type: "text/csv;charset=utf-8;" });
      downloadBlob(finalBlob, filename);
    } else {
      downloadBlob(blob, filename);
    }
  } catch (err: any) {
    console.warn(`Server export failed (${err.message}). Falling back to local roster export...`);
    if (fallbackRoster && fallbackRoster.length > 0) {
      const clientBlob = generateClientCSV(cleanDate, fallbackRoster);
      downloadBlob(clientBlob, `Mithra_Attendance_${cleanDate}.csv`);
    } else {
      throw err;
    }
  }
}
