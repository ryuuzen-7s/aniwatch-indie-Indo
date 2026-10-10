"""
api/models/anime.py — Pydantic schemas untuk Anime.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
#  OUTPUT SCHEMAS
# ═══════════════════════════════════════════════════════════
class AnimeMetadata(BaseModel):
    """Metadata anime."""
    title: Optional[str] = None
    title_jp: Optional[str] = None
    synopsis: Optional[str] = None
    poster_url: Optional[str] = None
    studio: Optional[str] = None
    producer: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    duration: Optional[str] = None
    release_date: Optional[str] = None
    total_episode: Optional[int] = None
    rating: Optional[float] = None
    genres: List[str] = Field(default_factory=list)
    info: Dict[str, Any] = Field(default_factory=dict)


class AnimeItem(BaseModel):
    """Anime tanpa episode (untuk list endpoint)."""
    id: int
    source: str
    slug: str
    url: Optional[str] = ""
    metadata: AnimeMetadata
    episode_count: int = 0
    scraped_at: Optional[str] = None
    updated_at: Optional[str] = None


class EpisodeBrief(BaseModel):
    """Episode singkat (untuk nested dalam anime)."""
    id: int
    slug: str
    url: Optional[str] = ""
    title: Optional[str] = ""
    episode_number: Optional[int] = None
    stream_host: Optional[str] = ""


class AnimeDetail(BaseModel):
    """Anime lengkap dengan episodes."""
    id: int
    source: str
    slug: str
    url: Optional[str] = ""
    metadata: AnimeMetadata
    episodes: List[EpisodeBrief] = Field(default_factory=list)
    total_episodes: int = 0
    scraped_at: Optional[str] = None
    updated_at: Optional[str] = None


# ═══════════════════════════════════════════════════════════
#  INTERNAL BUILDER
# ═══════════════════════════════════════════════════════════
def build_anime_metadata(anime) -> AnimeMetadata:
    """Konversi ORM Anime → AnimeMetadata."""
    return AnimeMetadata(
        title=anime.title or None,
        title_jp=anime.title_jp or None,
        synopsis=anime.synopsis or None,
        poster_url=anime.poster_url or None,
        studio=anime.studio or None,
        producer=anime.producer or None,
        type=anime.type or None,
        status=anime.status or None,
        duration=anime.duration or None,
        release_date=anime.release_date or None,
        total_episode=anime.total_episode,
        rating=anime.rating,
        genres=anime.genres or [],
        info=anime.info or {},
    )


def build_anime_item(anime, episode_count: int = 0) -> AnimeItem:
    """Konversi ORM → AnimeItem."""
    return AnimeItem(
        id=anime.id,
        source=anime.source,
        slug=anime.slug,
        url=anime.url or "",
        metadata=build_anime_metadata(anime),
        episode_count=episode_count,
        scraped_at=anime.scraped_at.isoformat() if anime.scraped_at else None,
        updated_at=anime.updated_at.isoformat() if anime.updated_at else None,
    )


def build_anime_detail(anime, episodes=None) -> AnimeDetail:
    """Konversi ORM → AnimeDetail (dengan episodes)."""
    ep_list = []
    if episodes:
        for ep in episodes:
            ep_list.append(EpisodeBrief(
                id=ep.id,
                slug=ep.slug,
                url=ep.url or "",
                title=ep.title or "",
                episode_number=ep.episode_number,
                stream_host=ep.stream_host or "",
            ))

    return AnimeDetail(
        id=anime.id,
        source=anime.source,
        slug=anime.slug,
        url=anime.url or "",
        metadata=build_anime_metadata(anime),
        episodes=ep_list,
        total_episodes=len(ep_list),
        scraped_at=anime.scraped_at.isoformat() if anime.scraped_at else None,
        updated_at=anime.updated_at.isoformat() if anime.updated_at else None,
    )