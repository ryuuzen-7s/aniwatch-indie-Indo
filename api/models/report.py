"""
api/models/report.py — Schema untuk report.
"""
from typing import Optional

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Body untuk POST /share/errorid/{slug}."""
    url: Optional[str] = Field(None, description="URL link yang bermasalah")
    reason: str = Field(..., min_length=3, max_length=500, description="Alasan report")
    quality: Optional[str] = Field(None, description="Kualitas (mis. 'Mp4 720p')")
    host: Optional[str] = Field(None, description="Host (mis. 'Mega')")


class ReportResponse(BaseModel):
    """Response report."""
    id: int
    slug: str
    type: str
    url: Optional[str] = None
    reason: str
    resolved: bool = False
    created_at: Optional[str] = None