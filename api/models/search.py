"""
api/models/search.py — Pydantic schemas untuk Search.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """Item hasil pencarian."""
    id: int
    source: str
    slug: str
    title: Optional[str] = ""
    title_jp: Optional[str] = ""
    poster_url: Optional[str] = ""
    studio: Optional[str] = ""
    type: Optional[str] = ""
    status: Optional[str] = ""
    total_episode: Optional[int] = None
    genres: List[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Response untuk /share/query."""
    query: str
    source: Optional[str] = None
    results: List[SearchResultItem] = Field(default_factory=list)
    total: int = 0
    from_cache: bool = False


def build_search_item(anime) -> SearchResultItem:
    """Konversi ORM Anime → SearchResultItem."""
    return SearchResultItem(
        id=anime.id,
        source=anime.source,
        slug=anime.slug,
        title=anime.title or "",
        title_jp=anime.title_jp or "",
        poster_url=anime.poster_url or "",
        studio=anime.studio or "",
        type=anime.type or "",
        status=anime.status or "",
        total_episode=anime.total_episode,
        genres=anime.genres or [],
    )