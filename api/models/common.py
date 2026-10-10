"""
api/models/common.py — Response wrapper & schema umum.
"""
from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar, List

from pydantic import BaseModel, Field


T = TypeVar("T")


# ═══════════════════════════════════════════════════════════
#  META
# ═══════════════════════════════════════════════════════════
class MetaInfo(BaseModel):
    """Metadata untuk setiap response."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cached: bool = False
    source: str = "db"  # "memory" | "db" | "live"
    duration_ms: int = 0


class PaginationMeta(BaseModel):
    """Metadata untuk response paginated."""
    total: int = 0
    page: int = 1
    per_page: int = 20
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False


class ErrorDetail(BaseModel):
    """Detail error."""
    code: str
    message: str
    status: int
    details: dict = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
#  RESPONSE WRAPPER
# ═══════════════════════════════════════════════════════════
class APIResponse(BaseModel, Generic[T]):
    """Response standar API."""
    success: bool
    data: Optional[T] = None
    meta: MetaInfo = Field(default_factory=MetaInfo)
    error: Optional[ErrorDetail] = None


# ═══════════════════════════════════════════════════════════
#  BUILDER HELPERS
# ═══════════════════════════════════════════════════════════
def success_response(
    data: Any,
    cached: bool = False,
    source: str = "db",
    duration_ms: int = 0,
) -> dict:
    """Bangun response sukses."""
    return {
        "success": True,
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": cached,
            "source": source,
            "duration_ms": duration_ms,
        },
        "error": None,
    }


def error_response(
    code: str,
    message: str,
    status: int = 500,
    details: Optional[dict] = None,
) -> dict:
    """Bangun response error."""
    return {
        "success": False,
        "data": None,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "error": {
            "code": code,
            "message": message,
            "status": status,
            "details": details or {},
        },
    }


def paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    per_page: int = 20,
    cached: bool = False,
) -> dict:
    """Bangun response dengan pagination."""
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return {
        "success": True,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": cached,
            "source": "db",
        },
        "error": None,
    }