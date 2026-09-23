"""Attendance Service covering daily, bulk, monthly calculations, and duplicate prevention."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from app.core.logging import logger
from app.models.activity import ActivityAction
from app.models.attendance import AttendanceRecordModel, AttendanceStatus
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    BulkAttendanceRequest,
    BulkAttendanceResponse,
    BulkAttendanceSummary,
    MemberAttendanceHistoryResponse,
    MonthlyAttendanceRow,
)
from app.services.activity_service import log_activity
from app.utils.calculations import calculate_attendance_percentage, summarize_attendance_statuses
from app.utils.validators import sanitize_member_id, validate_iso_date, validate_month_year


def get_attendance_by_id(db: Any, attendance_id: str) -> Dict[str, Any]:
    """Retrieve attendance record by document ID or raise 404."""
    doc = db.collection("attendance").document(attendance_id).get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": f"Attendance record '{attendance_id}' not found.", "error": "ATTENDANCE_NOT_FOUND"},
        )
    return doc.to_dict()


def create_attendance_record(
    db: Any,
    attendance_in: AttendanceCreate,
    admin_id: str,
    admin_name: str,
) -> Dict[str, Any]:
    """
    Create a single attendance record with deterministic document ID.
    Rejects duplicate attendance for memberId + date with HTTP 409.
    """
    clean_member_id = sanitize_member_id(attendance_in.memberId)
    date_str = validate_iso_date(attendance_in.date)

    # Validate member exists
    member_doc = db.collection("members").document(clean_member_id).get()
    if not member_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": f"Member with ID '{clean_member_id}' does not exist.",
                "error": "MEMBER_NOT_FOUND",
            },
        )
    member_data = member_doc.to_dict()

    # Determine department
    department_id = attendance_in.departmentId or member_data.get("departmentId")
    if not department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Department ID could not be resolved.", "error": "MISSING_DEPARTMENT"},
        )

    # Deterministic ID check for duplicate prevention
    doc_id = AttendanceRecordModel.generate_id(clean_member_id, date_str)
    existing_doc = db.collection("attendance").document(doc_id).get()

    if existing_doc.exists:
        logger.warning(f"Duplicate attendance rejected for member {clean_member_id} on {date_str}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already exists for this member and date.",
        )

    now = datetime.now(timezone.utc).isoformat()
    record = AttendanceRecordModel(
        attendanceId=doc_id,
        memberId=clean_member_id,
        date=date_str,
        status=attendance_in.status,
        departmentId=department_id,
        markedBy=admin_name,
        createdAt=now,
        updatedAt=now,
    ).model_dump(mode="json")

    db.collection("attendance").document(doc_id).set(record)

    log_activity(
        db=db,
        admin_id=admin_id,
        admin_name=admin_name,
        action=ActivityAction.ATTENDANCE_CREATED,
        target_type="ATTENDANCE",
        target_id=doc_id,
        metadata={"memberId": clean_member_id, "date": date_str, "status": attendance_in.status.value},
    )

    record["memberName"] = member_data.get("name")
    return record


def query_attendance_records(
    db: Any,
    date: Optional[str] = None,
    department_id: Optional[str] = None,
    member_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Query attendance records with supported filters."""
    query = db.collection("attendance")

    if date:
        clean_date = validate_iso_date(date)
        query = query.where("date", "==", clean_date)
    if department_id:
        query = query.where("departmentId", "==", department_id)
    if member_id:
        clean_member_id = sanitize_member_id(member_id)
        query = query.where("memberId", "==", clean_member_id)
    if status_filter:
        query = query.where("status", "==", status_filter.upper())

    docs = query.stream()
    records = [d.to_dict() for d in docs]

    # Pre-fetch lookup for member names and department names
    member_docs = db.collection("members").stream()
    member_lookup = {m.to_dict().get("memberId"): m.to_dict().get("name") for m in member_docs}

    dept_docs = db.collection("departments").stream()
    dept_lookup = {d.to_dict().get("departmentId"): d.to_dict().get("name") for d in dept_docs}

    for r in records:
        r["memberName"] = member_lookup.get(r.get("memberId"), "Unknown")
        r["departmentName"] = dept_lookup.get(r.get("departmentId"), "Unknown")

    records.sort(key=lambda x: (x.get("date", ""), x.get("memberId", "")), reverse=True)
    return records[:limit]


def update_attendance_record(
    db: Any,
    attendance_id: str,
    attendance_in: AttendanceUpdate,
    admin_id: str,
    admin_name: str,
) -> Dict[str, Any]:
    """Update an existing attendance status."""
    existing = get_attendance_by_id(db, attendance_id)

    now = datetime.now(timezone.utc).isoformat()
    old_status = existing.get("status")
    new_status = attendance_in.status.value

    db.collection("attendance").document(attendance_id).update({
        "status": new_status,
        "markedBy": admin_name,
        "updatedAt": now,
    })

    log_activity(
        db=db,
        admin_id=admin_id,
        admin_name=admin_name,
        action=ActivityAction.ATTENDANCE_UPDATED,
        target_type="ATTENDANCE",
        target_id=attendance_id,
        metadata={"oldStatus": old_status, "newStatus": new_status, "memberId": existing.get("memberId")},
    )

    return get_attendance_by_id(db, attendance_id)


def delete_attendance_record(
    db: Any,
    attendance_id: str,
    admin_id: str,
    admin_name: str,
) -> None:
    """Delete an attendance record (President-only)."""
    existing = get_attendance_by_id(db, attendance_id)

    db.collection("attendance").document(attendance_id).delete()

    log_activity(
        db=db,
        admin_id=admin_id,
        admin_name=admin_name,
        action=ActivityAction.ATTENDANCE_UPDATED,
        target_type="ATTENDANCE",
        target_id=attendance_id,
        metadata={"deleted": True, "date": existing.get("date"), "memberId": existing.get("memberId")},
    )


def process_bulk_attendance(
    db: Any,
    bulk_request: BulkAttendanceRequest,
    admin_id: str,
    admin_name: str,
) -> BulkAttendanceResponse:
    """
    Process bulk attendance submission for multiple members.
    Validates each record, skips or reports duplicates, handles partial failures safely.
    """
    date_str = validate_iso_date(bulk_request.date)
    successful: List[str] = []
    duplicates: List[str] = []
    failed: List[Dict[str, str]] = []

    # Pre-fetch all members into a quick lookup dictionary
    all_members = {m.to_dict().get("memberId"): m.to_dict() for m in db.collection("members").stream()}

    now = datetime.now(timezone.utc).isoformat()
    batch = db.batch()
    batch_count = 0

    for item in bulk_request.records:
        clean_id = sanitize_member_id(item.memberId)

        if clean_id not in all_members:
            failed.append({"memberId": clean_id, "reason": "Member does not exist."})
            continue

        member = all_members[clean_id]
        if member.get("status") != "ACTIVE":
            failed.append({"memberId": clean_id, "reason": "Member is inactive."})
            continue

        dept_id = member.get("departmentId", "GENERAL")
        doc_id = AttendanceRecordModel.generate_id(clean_id, date_str)

        # Check existing by (memberId, date) or by doc_id
        existing_docs = list(
            db.collection("attendance").where("memberId", "==", clean_id).where("date", "==", date_str).stream()
        )
        if not existing_docs:
            single_doc = db.collection("attendance").document(doc_id).get()
            if single_doc.exists:
                existing_docs = [single_doc]

        if existing_docs:
            for ex in existing_docs:
                ex_ref = db.collection("attendance").document(ex.id)
                update_payload = {
                    "status": item.status.value,
                    "markedBy": admin_name,
                    "updatedAt": now,
                }
                batch.update(ex_ref, update_payload)
            successful.append(clean_id)
            batch_count += 1
            continue

        record_data = AttendanceRecordModel(
            attendanceId=doc_id,
            memberId=clean_id,
            date=date_str,
            status=item.status,
            departmentId=dept_id,
            markedBy=admin_name,
            createdAt=now,
            updatedAt=now,
        ).model_dump(mode="json")

        batch.set(db.collection("attendance").document(doc_id), record_data)
        successful.append(clean_id)
        batch_count += 1

    if batch_count > 0:
        batch.commit()
        log_activity(
            db=db,
            admin_id=admin_id,
            admin_name=admin_name,
            action=ActivityAction.ATTENDANCE_CREATED,
            target_type="ATTENDANCE_BULK",
            target_id=date_str,
            metadata={
                "date": date_str,
                "successfulCount": len(successful),
                "duplicateCount": len(duplicates),
                "failedCount": len(failed),
            },
        )

    summary = BulkAttendanceSummary(
        total=len(bulk_request.records),
        successful=len(successful),
        duplicates=len(duplicates),
        failed=len(failed),
    )

    return BulkAttendanceResponse(
        summary=summary,
        successful=successful,
        duplicates=duplicates,
        failed=failed,
    )


def mark_all_active_present(
    db: Any,
    date_str: str,
    department_id: Optional[str],
    admin_id: str,
    admin_name: str,
) -> BulkAttendanceResponse:
    """Convenience helper to mark all active members present for a given date."""
    date_clean = validate_iso_date(date_str)

    query = db.collection("members").where("status", "==", "ACTIVE")
    if department_id:
        query = query.where("departmentId", "==", department_id)

    members = [d.to_dict() for d in query.stream()]
    records = [{"memberId": m["memberId"], "status": AttendanceStatus.PRESENT} for m in members]

    req = BulkAttendanceRequest(date=date_clean, records=records)
    return process_bulk_attendance(db, req, admin_id=admin_id, admin_name=admin_name)


def get_monthly_attendance_summary(
    db: Any,
    month: int,
    year: int,
    department_id: Optional[str] = None,
    member_id: Optional[str] = None,
) -> List[MonthlyAttendanceRow]:
    """
    Calculate and aggregate monthly attendance for members.
    Attendance Percentage = ((Present Days + Late Days) / Total Days) * 100
    """
    month, year = validate_month_year(month, year)
    prefix = f"{year:04d}-{month:02d}"

    # Fetch active/relevant members
    members_query = db.collection("members")
    if department_id:
        members_query = members_query.where("departmentId", "==", department_id)
    if member_id:
        members_query = members_query.where("memberId", "==", sanitize_member_id(member_id))

    members = [m.to_dict() for m in members_query.stream()]

    # Fetch department names
    dept_docs = db.collection("departments").stream()
    dept_lookup = {d.to_dict().get("departmentId"): d.to_dict().get("name") for d in dept_docs}

    # Fetch attendance records for this month prefix
    # Attendance date is stored in YYYY-MM-DD
    all_attendance_docs = db.collection("attendance").stream()
    attendance_by_member: Dict[str, List[Dict[str, Any]]] = {}

    for doc in all_attendance_docs:
        rec = doc.to_dict()
        rec_date = rec.get("date", "")
        if rec_date.startswith(prefix):
            mid = rec.get("memberId")
            if mid:
                attendance_by_member.setdefault(mid, []).append(rec)

    rows: List[MonthlyAttendanceRow] = []
    for member in members:
        mid = member.get("memberId")
        recs = attendance_by_member.get(mid, [])
        statuses = [r.get("status") for r in recs]
        present, late, absent, total = summarize_attendance_statuses(statuses)
        percentage = calculate_attendance_percentage(present, late, total)

        rows.append(
            MonthlyAttendanceRow(
                memberId=mid,
                memberName=member.get("name", "Unknown"),
                departmentId=member.get("departmentId", ""),
                departmentName=dept_lookup.get(member.get("departmentId"), "Unknown"),
                presentDays=present,
                absentDays=absent,
                lateDays=late,
                totalAttendanceDays=total,
                attendancePercentage=percentage,
            )
        )

    rows.sort(key=lambda x: x.memberName.lower())
    return rows


def get_member_attendance_history(
    db: Any,
    member_id: str,
    month: Optional[int] = None,
    year: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> MemberAttendanceHistoryResponse:
    """Retrieve complete attendance history and overall analytics for a member."""
    clean_id = sanitize_member_id(member_id)
    member_doc = db.collection("members").document(clean_id).get()
    if not member_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": f"Member '{clean_id}' not found.", "error": "MEMBER_NOT_FOUND"},
        )
    member = member_doc.to_dict()

    dept_doc = db.collection("departments").document(member.get("departmentId", "")).get()
    dept_name = dept_doc.to_dict().get("name") if dept_doc.exists else "Unknown"

    records_query = db.collection("attendance").where("memberId", "==", clean_id).stream()
    history_records = [r.to_dict() for r in records_query]

    # Filters
    filtered = []
    for r in history_records:
        r_date = r.get("date", "")
        if month and year:
            prefix = f"{year:04d}-{month:02d}"
            if not r_date.startswith(prefix):
                continue
        if start_date and r_date < start_date:
            continue
        if end_date and r_date > end_date:
            continue
        r["memberName"] = member.get("name")
        r["departmentName"] = dept_name
        filtered.append(r)

    filtered.sort(key=lambda x: x.get("date", ""), reverse=True)

    statuses = [r.get("status") for r in filtered]
    present, late, absent, total = summarize_attendance_statuses(statuses)
    overall_pct = calculate_attendance_percentage(present, late, total)

    return MemberAttendanceHistoryResponse(
        memberId=clean_id,
        memberName=member.get("name"),
        departmentId=member.get("departmentId", ""),
        departmentName=dept_name,
        overallAttendancePercentage=overall_pct,
        totalSessions=total,
        presentCount=present,
        absentCount=absent,
        lateCount=late,
        history=[AttendanceResponse(**r) for r in filtered],
    )
