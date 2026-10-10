"""
api/models/season.py — Schema untuk season.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class SeasonAnimeItem(BaseModel):
    """Anime dalam season."""
    id: int
    slug: str
    title: Optional[str] = ""
    poster_url: Optional[str] = ""
    studio: Optional[str] = ""
    type: Optional[str] = ""
    status: Optional[str] = ""
    release_date: Optional[str] = ""
    genres: List[str] = Field(default_factory=list)


class SeasonResponse(BaseModel):
    """Response untuk /share/season/{season}."""
    season: str
    year: Optional[int] = None
    month_range: Optional[str] = None
    results: List[SeasonAnimeItem] = Field(default_factory=list)
    total: int = 0