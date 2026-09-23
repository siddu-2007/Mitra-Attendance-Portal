"""Schemas for Member operations and filters."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.member import MemberStatus


class MemberCreate(BaseModel):
    memberId: str = Field(..., min_length=2, max_length=50, description="Unique club member ID, e.g. 24PA1A4511")
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    departmentId: str = Field(..., description="ID of assigned department")
    academicYear: str = Field(..., min_length=1, max_length=50, description="e.g. 2nd Year or 2024-2025")
    joiningDate: str = Field(..., description="Date of joining in YYYY-MM-DD format")


class MemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    departmentId: Optional[str] = None
    academicYear: Optional[str] = None
    joiningDate: Optional[str] = None


class MemberStatusUpdate(BaseModel):
    status: MemberStatus


class MemberResponse(BaseModel):
    memberId: str
    name: str
    email: str
    phone: Optional[str] = None
    departmentId: str
    departmentName: Optional[str] = None
    academicYear: str
    joiningDate: str
    status: MemberStatus
    createdAt: str
    updatedAt: str
