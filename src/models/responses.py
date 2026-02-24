"""Standardized response formats.

All API responses use a consistent envelope format for predictability.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from src.constants import ResponseStatus

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    status: str = Field(default=ResponseStatus.SUCCESS, description="Response status")
    data: T | None = Field(default=None, description="Response payload")
    message: str | None = Field(default=None, description="Human-readable message")
    error: str | None = Field(default=None, description="Error details if status is error")
    meta: dict[str, Any] = Field(
        default_factory=dict, description="Metadata (pagination, counts, etc.)"
    )

    @classmethod
    def success(cls, data: T, message: str | None = None, **meta) -> "APIResponse[T]":
        """Create a successful response."""
        return cls(
            status=ResponseStatus.SUCCESS,
            data=data,
            message=message,
            meta=meta,
        )

    @classmethod
    def error(cls, error: str, message: str | None = None, **meta) -> "APIResponse[None]":
        """Create an error response."""
        return cls(
            status=ResponseStatus.ERROR,
            error=error,
            message=message or error,
            meta=meta,
        )

    @classmethod
    def partial(cls, data: T, error: str, **meta) -> "APIResponse[T]":
        """Create a partial success response."""
        return cls(
            status=ResponseStatus.PARTIAL,
            data=data,
            error=error,
            message=f"Partial success: {error}",
            meta=meta,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response with items and metadata."""

    items: list[T] = Field(description="List of items")
    total: int = Field(description="Total count")
    page: int = Field(default=1, description="Current page")
    per_page: int = Field(default=20, description="Items per page")
    has_more: bool = Field(default=False, description="Whether more items exist")

    @classmethod
    def from_list(
        cls,
        items: list[T],
        total: int | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> "PaginatedResponse[T]":
        """Create paginated response from list."""
        total = total or len(items)
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            has_more=total > (page * per_page),
        )


# Common response types
class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: str
    checks: dict[str, bool] = Field(default_factory=dict)


class ChatResponseData(BaseModel):
    """Chat response data."""

    response: str
    session_id: str
    model: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    preview_used: bool = False
    emotional_adaptation: str = "neutral"


class MemoryStatsResponse(BaseModel):
    """Memory statistics response."""

    total_memories: int
    by_type: dict[str, int]
    by_sector: dict[str, int] | None = None
    backend: str
    last_updated: str | None = None


class PackageOperationResponse(BaseModel):
    """Package operation response."""

    success: bool
    package: str
    operation: str  # install, remove, search
    output: str | None = None
    error: str | None = None
