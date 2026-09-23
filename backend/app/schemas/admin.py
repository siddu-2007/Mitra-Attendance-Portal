"""Schemas for Admin authentication and management."""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.admin import AdminRole, AdminStatus


class AdminResponse(BaseModel):
    uid: str
    name: str
    email: str
    role: AdminRole
    status: AdminStatus
    permissions: List[str]
    createdAt: str
    updatedAt: str


class AdminCreate(BaseModel):
    uid: str
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: AdminRole = AdminRole.ADMIN
    permissions: Optional[List[str]] = None


class AdminStatusUpdate(BaseModel):
    status: AdminStatus
