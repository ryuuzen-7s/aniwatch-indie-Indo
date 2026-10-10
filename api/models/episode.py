"""
api/models/episode.py — Pydantic schemas untuk Episode.
"""
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
#  STREAM & DOWNLOAD
# ═══════════════════════════════════════════════════════════
class StreamItem(BaseModel):
    """Link streaming."""
    host: str
    url: str
    quality: Optional[str] = "default"


class DownloadItem(BaseModel):
    """Link download."""
    id: Optional[int] = None
    quality: str
    host: str
    url: str
    final_url: Optional[str] = None
    final_host: Optional[str] = None
    status: Optional[int] = None
    is_alive: bool = True
    error: Optional[str] = None
    checked_at: Optional[str] = None


class DownloadsSummary(BaseModel):
    """Ringkasan download."""
    total: int = 0
    alive: int = 0
    dead: int = 0
    by_quality: Dict[str, int] = Field(default_factory=dict)
    by_host: Dict[str, int] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
#  EPISODE ITEMS
# ═══════════════════════════════════════════════════════════
class EpisodeItem(BaseModel):
    """Episode singkat (list)."""
    id: int
    anime_id: int
    slug: str
    url: Optional[str] = ""
    title: Optional[str] = ""
    episode_number: Optional[int] = None
    stream_host: Optional[str] = ""
    has_downloads: bool = False
    download_count: int = 0


class EpisodeDetail(BaseModel):
    """Episode lengkap dengan stream + download."""
    id: int
    anime_id: int
    anime_slug: Optional[str] = None
    anime_title: Optional[str] = None
    slug: str
    url: Optional[str] = ""
    title: Optional[str] = ""
    episode_number: Optional[int] = None
    streams: List[StreamItem] = Field(default_factory=list)
    downloads: List[DownloadItem] = Field(default_factory=list)
    downloads_summary: DownloadsSummary = Field(default_factory=DownloadsSummary)
    scraped_at: Optional[str] = None
    updated_at: Optional[str] = None


class EpisodeListResponse(BaseModel):
    """Response untuk /share/episodeid/{slug}."""
    anime_id: int
    anime_slug: str
    anime_title: Optional[str] = None
    episodes: List[EpisodeItem] = Field(default_factory=list)
    total: int = 0


# ═══════════════════════════════════════════════════════════
#  BUILDERS
# ═══════════════════════════════════════════════════════════
def build_episode_item(ep, download_count: int = 0) -> EpisodeItem:
    """Konversi ORM Episode → EpisodeItem."""
    return EpisodeItem(
        id=ep.id,
        anime_id=ep.anime_id,
        slug=ep.slug,
        url=ep.url or "",
        title=ep.title or "",
        episode_number=ep.episode_number,
        stream_host=ep.stream_host or "",
        has_downloads=download_count > 0,
        download_count=download_count,
    )


def build_download_item(dl) -> DownloadItem:
    """Konversi ORM DownloadLink → DownloadItem."""
    return DownloadItem(
        id=dl.id,
        quality=dl.quality or "",
        host=dl.host or "",
        url=dl.url or "",
        final_url=dl.final_url or None,
        final_host=dl.final_host or None,
        status=dl.status,
        is_alive=bool(dl.is_alive),
        error=dl.error or None,
        checked_at=dl.checked_at.isoformat() if dl.checked_at else None,
    )


def build_downloads_summary(downloads: List[DownloadItem]) -> DownloadsSummary:
    """Hitung ringkasan download."""
    alive = sum(1 for d in downloads if d.is_alive)
    dead = len(downloads) - alive

    by_quality: Dict[str, int] = {}
    by_host: Dict[str, int] = {}
    for d in downloads:
        by_quality[d.quality] = by_quality.get(d.quality, 0) + 1
        host = d.final_host or d.host
        by_host[host] = by_host.get(host, 0) + 1

    return DownloadsSummary(
        total=len(downloads),
        alive=alive,
        dead=dead,
        by_quality=by_quality,
        by_host=by_host,
    )


def build_episode_detail(ep, downloads: List = None, anime=None) -> EpisodeDetail:
    """Konversi ORM Episode → EpisodeDetail."""
    dl_items = [build_download_item(d) for d in (downloads or [])]

    # Stream dari field ORM (single stream)
    streams = []
    if ep.stream_url:
        streams.append(StreamItem(
            host=ep.stream_host or "unknown",
            url=ep.stream_url,
            quality="default",
        ))

    return EpisodeDetail(
        id=ep.id,
        anime_id=ep.anime_id,
        anime_slug=anime.slug if anime else None,
        anime_title=anime.title if anime else None,
        slug=ep.slug,
        url=ep.url or "",
        title=ep.title or "",
        episode_number=ep.episode_number,
        streams=streams,
        downloads=dl_items,
        downloads_summary=build_downloads_summary(dl_items),
        scraped_at=ep.scraped_at.isoformat() if ep.scraped_at else None,
        updated_at=ep.updated_at.isoformat() if ep.updated_at else None,
    )


def build_episode_list_response(anime, episodes_data: List) -> EpisodeListResponse:
    """
    Bangun response list episode.
    episodes_data = list of (episode_orm, download_count)
    """
    items = [
        build_episode_item(ep, dl_count)
        for ep, dl_count in episodes_data
    ]
    return EpisodeListResponse(
        anime_id=anime.id,
        anime_slug=anime.slug,
        anime_title=anime.title or None,
        episodes=items,
        total=len(items),
    )