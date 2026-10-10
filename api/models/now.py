"""
api/models/now.py — Schema untuk episode terbaru.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class NowAnimeItem(BaseModel):
    """Anime ongoing terbaru."""
    id: int
    slug: str
    title: Optional[str] = ""
    poster_url: Optional[str] = ""
    studio: Optional[str] = ""
    status: Optional[str] = ""
    total_episode: Optional[int] = None
    episode_count: int = 0
    latest_episode_number: Optional[int] = None
    updated_at: Optional[str] = None
    genres: List[str] = Field(default_factory=list)


class NowResponse(BaseModel):
    """Response untuk /share/now."""
    results: List[NowAnimeItem] = Field(default_factory=list)
    total: int = 0