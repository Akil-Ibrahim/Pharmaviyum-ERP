"""
Standardized response schemas
Best practice 2026: Consistent API response format
"""
from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, Any, List
from datetime import datetime, timezone

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    """
    Standard API response envelope
    
    All API responses follow this format:
    {
        "success": true,
        "data": {...},
        "meta": {...},
        "errors": null
    }
    """
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data")
    meta: Optional[dict[str, Any]] = Field(None, description="Metadata")
    errors: Optional[list[dict[str, Any]]] = Field(None, description="Error details")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Response timestamp"
    )
    
    @classmethod
    def success_response(cls, data: T, meta: Optional[dict] = None) -> "ResponseEnvelope[T]":
        """Create success response"""
        return cls(success=True, data=data, meta=meta)
    
    @classmethod
    def error_response(
        cls,
        message: str,
        code: str = "ERROR",
        details: Optional[dict] = None,
    ) -> "ResponseEnvelope[None]":
        """Create error response"""
        error = {"code": code, "message": message}
        if details:
            error["details"] = details
        
        return cls(success=False, data=None, errors=[error])


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    
    @classmethod
    def create(cls, page: int, page_size: int, total_items: int) -> "PaginationMeta":
        """Create pagination metadata"""
        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
        
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response wrapper
    
    Usage:
        return PaginatedResponse.create(items, page, page_size, total)
    """
    items: list[T] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    
    @classmethod
    def create(
        cls,
        items: list[T],
        page: int,
        page_size: int,
        total_items: int,
    ) -> "PaginatedResponse[T]":
        """Create paginated response"""
        return cls(
            items=items,
            pagination=PaginationMeta.create(page, page_size, total_items),
        )


class ErrorResponse(BaseModel):
    """Error response model"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional details")
