"""Schemas for Department operations."""

from typing import Optional
from pydantic import BaseModel, Field
from app.models.department import DepartmentStatus


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Department name")


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)


class DepartmentStatusUpdate(BaseModel):
    status: DepartmentStatus


class DepartmentResponse(BaseModel):
    departmentId: str
    name: str
    status: DepartmentStatus
    createdAt: str
    updatedAt: Optional[str] = None
