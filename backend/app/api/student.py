"""Student Portal API Endpoints."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.firebase import get_db
from app.core.security import get_current_student
from app.schemas.common import APIResponse
from app.services.attendance_service import get_member_attendance_history

router = APIRouter()


@router.get("/me", summary="Get Current Student Profile")
async def get_student_profile(
    current_student: Dict[str, Any] = Depends(get_current_student),
    db: Any = Depends(get_db),
):
    """Retrieve authenticated student's profile, department assignment, and academic details."""
    dept_id = current_student.get("departmentId")
    dept_name = current_student.get("departmentName") or "Club Wing"
    if dept_id:
        dept_snap = db.collection("departments").document(dept_id).get()
        if not dept_snap.exists and dept_id.startswith("dept_"):
            dept_snap = db.collection("departments").document(dept_id[5:]).get()
        elif not dept_snap.exists:
            dept_snap = db.collection("departments").document(f"dept_{dept_id}").get()
        if dept_snap.exists:
            dept_name = dept_snap.to_dict().get("name", dept_name)

    student_data = dict(current_student)
    student_data["departmentName"] = dept_name

    return APIResponse(
        success=True,
        message="Student profile retrieved successfully.",
        data=student_data,
    )


@router.get("/me/attendance", summary="Get Student Personal Attendance History")
async def get_student_attendance(
    current_student: Dict[str, Any] = Depends(get_current_student),
    db: Any = Depends(get_db),
):
    """Retrieve full personal attendance history, session logs, and attendance percentage."""
    member_id = current_student.get("memberId")
    history = get_member_attendance_history(db=db, member_id=member_id)

    return APIResponse(
        success=True,
        message=f"Personal attendance roll retrieved for {member_id}.",
        data=history,
    )


@router.get("/me/team", summary="Get Department Team Roster")
async def get_student_team(
    current_student: Dict[str, Any] = Depends(get_current_student),
    db: Any = Depends(get_db),
):
    """Retrieve fellow club members and wing details for the student's assigned department."""
    dept_id = current_student.get("departmentId")
    if not dept_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "No department assigned to this student.", "error": "NO_DEPARTMENT"}
        )

    # Fetch department info
    dept_snap = db.collection("departments").document(dept_id).get()
    if not dept_snap.exists and dept_id.startswith("dept_"):
        dept_snap = db.collection("departments").document(dept_id[5:]).get()
    elif not dept_snap.exists:
        dept_snap = db.collection("departments").document(f"dept_{dept_id}").get()

    dept_name = dept_snap.to_dict().get("name") if dept_snap.exists else (current_student.get("departmentName") or "Club Wing")
    dept_info = {"name": dept_name, "departmentId": dept_id}

    # Fetch all members in this department
    member_docs = db.collection("members").where("departmentId", "==", dept_id).stream()
    teammates: List[Dict[str, Any]] = []
    for doc in member_docs:
        m = doc.to_dict()
        teammates.append({
            "memberId": m.get("memberId"),
            "name": m.get("name"),
            "email": m.get("email"),
            "academicYear": m.get("academicYear"),
            "isMe": m.get("memberId") == current_student.get("memberId"),
            "status": m.get("status"),
        })

    # Sort so the logged-in student appears first, followed by others alphabetically
    teammates.sort(key=lambda x: (not x["isMe"], x["name"].lower()))

    return APIResponse(
        success=True,
        message=f"Team members retrieved for {dept_info.get('name')}.",
        data={
            "departmentId": dept_id,
            "departmentName": dept_info.get("name"),
            "totalMembers": len(teammates),
            "teamMembers": teammates,
        },
    )
