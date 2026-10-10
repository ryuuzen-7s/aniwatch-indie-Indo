"""
api/models/empty.py — Schema untuk empty (force scrape).
"""
from typing import Optional

from pydantic import BaseModel, Field


class EmptyRequest(BaseModel):
    """Body untuk POST /share/empty/{slug}."""
    source: Optional[str] = Field(None, description="Source provider")
    follow_all: bool = Field(True, description="Scrape semua episode")


class EmptyResponse(BaseModel):
    """Response force scrape."""
    slug: str
    source: str
    scraped: bool = False
    anime: int = 0
    episodes: int = 0
    downloads: int = 0
    message: Optional[str] = None