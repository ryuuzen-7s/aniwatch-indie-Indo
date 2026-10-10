"""
api/services/episode_service.py — Business logic untuk Episode.
"""
import logging
import time
from typing import Optional, List, Tuple

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from config import settings
from db.models import Anime, Episode, DownloadLink
from db.repository import AnimeRepository, EpisodeRepository, DownloadRepository
from api.exceptions import (
    AnimeNotFoundError, EpisodeNotFoundError,
)
from api.services.anime_service import get_anime


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  GET EPISODE LIST
# ═══════════════════════════════════════════════════════════
def get_episode_list(
    db: Session,
    slug: str,
    source: Optional[str] = None,
) -> Tuple[Anime, List[Tuple[Episode, int]]]:
    """
    Ambil list episode untuk anime.
    Auto-scrape kalau anime belum ada (via get_anime).

    Returns:
        (anime, [(episode, download_count), ...])
    """
    # Pastikan anime ada (auto-scrape kalau perlu)
    anime, _ = get_anime(db, slug, source=source, refresh=False)

    # Ambil episodes
    episodes = list(db.execute(
        select(Episode)
        .where(Episode.anime_id == anime.id)
        .order_by(Episode.episode_number.asc().nulls_last())
    ).scalars())

    # Hitung download count per episode (batch, biar efisien)
    ep_ids = [ep.id for ep in episodes]
    dl_counts = {}
    if ep_ids:
        rows = db.execute(
            select(DownloadLink.episode_id, func.count())
            .where(DownloadLink.episode_id.in_(ep_ids))
            .group_by(DownloadLink.episode_id)
        ).all()
        dl_counts = {ep_id: count for ep_id, count in rows}

    episodes_data = [(ep, dl_counts.get(ep.id, 0)) for ep in episodes]
    return anime, episodes_data


# ═══════════════════════════════════════════════════════════
#  GET EPISODE DETAIL
# ═══════════════════════════════════════════════════════════
def get_episode_by_number(
    db: Session,
    anime_slug: str,
    episode_number: int,
    source: Optional[str] = None,
) -> Tuple[Anime, Episode, List[DownloadLink]]:
    """
    Ambil episode berdasarkan nomor & anime slug.

    Returns:
        (anime, episode, downloads)

    Raises:
        AnimeNotFoundError, EpisodeNotFoundError
    """
    # Pastikan anime ada
    anime, _ = get_anime(db, anime_slug, source=source, refresh=False)

    # Cari episode
    episode = db.execute(
        select(Episode)
        .where(Episode.anime_id == anime.id)
        .where(Episode.episode_number == episode_number)
    ).scalar_one_or_none()

    if not episode:
        raise EpisodeNotFoundError(
            f"Episode {episode_number} dari '{anime_slug}' tidak ditemukan",
            details={
                "anime_slug": anime_slug,
                "episode_number": episode_number,
                "available": [ep.episode_number for ep in
                              db.execute(select(Episode).where(Episode.anime_id == anime.id)).scalars()],
            },
        )

    # Ambil downloads
    downloads = list(db.execute(
        select(DownloadLink)
        .where(DownloadLink.episode_id == episode.id)
        .order_by(DownloadLink.quality, DownloadLink.host)
    ).scalars())

    return anime, episode, downloads


def get_episode_by_slug(
    db: Session,
    episode_slug: str,
) -> Tuple[Optional[Anime], Episode, List[DownloadLink]]:
    """
    Ambil episode berdasarkan slug episode langsung.
    """
    episode = db.execute(
        select(Episode).where(Episode.slug == episode_slug)
    ).scalar_one_or_none()

    if not episode:
        raise EpisodeNotFoundError(
            f"Episode '{episode_slug}' tidak ditemukan",
            details={"slug": episode_slug},
        )

    anime = db.get(Anime, episode.anime_id)
    downloads = list(db.execute(
        select(DownloadLink).where(DownloadLink.episode_id == episode.id)
    ).scalars())

    return anime, episode, downloads