"""Attendance and Statistical Calculation Utilities."""

from typing import Any, Iterable, Tuple


def calculate_attendance_percentage(present_days: int, late_days: int, total_days: int) -> float:
    """
    Calculate attendance percentage according to VIT Mithra V1 business rules:
    - PRESENT is counted (1.0)
    - LATE is counted (1.0)
    - ABSENT is not counted (0.0)
    Formula: ((Present + Late) / Total) * 100
    Rounded to 2 decimal places. Returns 0.0 if total_days is 0.
    """
    if total_days <= 0:
        return 0.0

    attended_days = present_days + late_days
    # Guard against illogical data
    attended_days = min(attended_days, total_days)

    percentage = (attended_days / total_days) * 100.0
    return round(percentage, 2)


def summarize_attendance_statuses(statuses: Iterable[Any]) -> Tuple[int, int, int, int]:
    """
    Given an iterable of status strings or Enums, return:
    (present_count, late_count, absent_count, total_count)
    """
    present = 0
    late = 0
    absent = 0

    for s in statuses:
        if not s:
            continue
        val = s.value if hasattr(s, "value") else str(s)
        # Handle stringified enum representations like AttendanceStatus.PRESENT
        val = str(val).split(".")[-1].strip().upper()
        if val == "PRESENT":
            present += 1
        elif val == "LATE":
            late += 1
        elif val == "ABSENT":
            absent += 1

    total = present + late + absent
    return present, late, absent, total
