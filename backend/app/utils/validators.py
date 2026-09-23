"""Validation and formatting helpers for dates, IDs, and query parameters."""

import re
from datetime import datetime, timezone
from typing import Optional, Tuple


def validate_iso_date(date_str: str) -> str:
    """Validate that date is in strictly YYYY-MM-DD format."""
    if not date_str or not isinstance(date_str, str):
        raise ValueError("Date string is required.")
    try:
        parsed = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.")


def validate_month_year(month: int, year: int) -> Tuple[int, int]:
    """Validate month (1-12) and year (2000-2100)."""
    if not (1 <= month <= 12):
        raise ValueError(f"Invalid month {month}. Expected integer between 1 and 12.")
    if not (2000 <= year <= 2100):
        raise ValueError(f"Invalid year {year}. Expected integer between 2000 and 2100.")
    return month, year


def sanitize_member_id(member_id: str) -> str:
    """Ensure member ID is alphanumeric uppercase string."""
    cleaned = re.sub(r"[^A-Za-z0-9\-_]", "", member_id.strip()).upper()
    if not cleaned:
        raise ValueError("Member ID cannot be empty or solely invalid characters.")
    return cleaned


def get_current_utc_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def get_today_date_str() -> str:
    """Return current date string in YYYY-MM-DD format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")
