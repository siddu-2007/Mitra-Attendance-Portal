"""Standardized API Response Envelopes and Error Schemas."""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard success API response envelope."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None


class APIErrorResponse(BaseModel):
    """Standard error response structure."""
    success: bool = False
    message: str
    error: str
    details: Optional[Any] = None


class PaginatedData(BaseModel, Generic[T]):
    """Generic container for paginated or filtered list results."""
    items: List[T]
    total: int
    limit: Optional[int] = None
    offset: Optional[int] = None
