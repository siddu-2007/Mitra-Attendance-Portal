"""Unit tests for calculation logic and mathematical edge cases."""

from app.utils.calculations import calculate_attendance_percentage, summarize_attendance_statuses


def test_zero_total_days():
    """Zero total days safely returns 0.0 without DivisionByZeroError."""
    assert calculate_attendance_percentage(0, 0, 0) == 0.0
    assert calculate_attendance_percentage(5, 0, 0) == 0.0


def test_full_attendance():
    """All present equals 100.0%."""
    assert calculate_attendance_percentage(10, 0, 10) == 100.0


def test_present_and_late_counted():
    """Under VIT Mithra V1 rules, both PRESENT and LATE are counted."""
    # 7 Present + 3 Late out of 10 = 100.0%
    assert calculate_attendance_percentage(7, 3, 10) == 100.0

    # 4 Present + 2 Late out of 10 = 60.0%
    assert calculate_attendance_percentage(4, 2, 10) == 60.0


def test_rounding_two_decimal_places():
    """Ensure floating points are rounded to exactly two decimal places."""
    # 1/3 = 33.333333% -> 33.33%
    assert calculate_attendance_percentage(1, 0, 3) == 33.33

    # 2/3 = 66.666666% -> 66.67%
    assert calculate_attendance_percentage(2, 0, 3) == 66.67

    # 5/7 = 71.42857% -> 71.43%
    assert calculate_attendance_percentage(5, 0, 7) == 71.43


def test_status_summarization():
    statuses = ["PRESENT", "present", "LATE", "late", "ABSENT", "absent", "PRESENT"]
    p, l, ab, tot = summarize_attendance_statuses(statuses)
    assert p == 3
    assert l == 2
    assert ab == 2
    assert tot == 7
