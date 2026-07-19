"""
Common response schemas.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Generic, TypeVar, Optional, Dict, Any

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response format."""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    timestamp: datetime


class ErrorDetail(BaseModel):
    """Error details."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: ErrorDetail
    timestamp: datetime
