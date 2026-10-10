"""
api/services/anime_service.py — Business logic untuk anime.

Alur hybrid:
1. Cek DB dulu
2. Kalau tidak ada / refresh / stale → live scrape
3. Simpan ke DB, return
"""
import logging
import time
from typing import Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from config import settings
from db.models import Anime, Episode
from db.repository import AnimeRepository, save_scrape_result
from core.pipeline import scrape_anime  # akan dibuat di batch ini juga
from api.exceptions import AnimeNotFoundError, ScrapeError, UpstreamError


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════
STALE_AFTER_DAYS = 7  # Auto-refresh kalau data > 7 hari


# ═══════════════════════════════════════════════════════════
#  GET ANIME (hybrid)
# ═══════════════════════════════════════════════════════════
def get_anime(
    db: Session,
    slug: str,
    source: Optional[str] = None,
    refresh: bool = False,
) -> Tuple[Anime, str]:
    """Ambil anime dengan cache hybrid."""
    from cache.strategy import get_anime_cached, cache_anime, invalidate_anime

    source = (source or settings.default_source).lower()

    # Kalau refresh, hapus cache
    if refresh:
        invalidate_anime(slug, source)

    # 1. Cek cache
    if not refresh:
        cached = get_anime_cached(slug, source)
        if cached:
            # Bangun ORM object dari dict cache
            anime = AnimeRepository.get_by_slug(db, slug)
            if anime:
                return anime, "cache"

    # 2. Cek DB
    if not refresh:
        anime = AnimeRepository.get_by_slug(db, slug)
        if anime and anime.title:
            # Cache ke memory+file
            try:
                cache_anime(slug, source, {
                    "id": anime.id,
                    "slug": anime.slug,
                    "title": anime.title,
                    "studio": anime.studio,
                    "genres": anime.genres,
                    "poster_url": anime.poster_url,
                })
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            return anime, "db"

    # 3. Live scrape
    logger.info(f"[{slug}] Scrape live...")

    try:
        result = scrape_anime(
            path_or_url=f"/anime/{slug}",
            source=source,
            follow_all=True,
            resolve=False,
            filter_dead=False,
        )
    except Exception as e:
        old = AnimeRepository.get_by_slug(db, slug)
        if old and old.title:
            return old, "db"
        raise AnimeNotFoundError(
            f"Anime '{slug}' tidak ditemukan & scrape gagal",
            details={"slug": slug, "error": str(e)[:200]},
        )

    # Validasi
    if not result.get("metadata", {}).get("title"):
        raise AnimeNotFoundError(
            f"Scrape '{slug}' menghasilkan data kosong",
            details={"slug": slug},
        )

    # Simpan
    try:
        save_scrape_result(result)
    except Exception as e:
        raise ScrapeError(f"Gagal simpan: {str(e)[:200]}")

    # Cache
    invalidate_anime(slug, source)

    anime = AnimeRepository.get_by_slug(db, slug)
    if not anime:
        raise AnimeNotFoundError(f"Anime '{slug}' tidak ada setelah scrape")

    return anime, "live"
# ═══════════════════════════════════════════════════════════
#  HELPER: COUNT EPISODES
# ═══════════════════════════════════════════════════════════
def count_episodes(db: Session, anime_id: int) -> int:
    """Hitung jumlah episode untuk anime."""
    return db.scalar(
        select(func.count()).select_from(Episode).where(Episode.anime_id == anime_id)
    ) or 0


def get_episodes(db: Session, anime_id: int) -> list:
    """Ambil semua episode dari anime."""
    return list(db.execute(
        select(Episode)
        .where(Episode.anime_id == anime_id)
        .order_by(Episode.episode_number.asc().nulls_last())
    ).scalars())


# ═══════════════════════════════════════════════════════════
#  FORCE SCRAPE (untuk POST /share/empty/{slug})
# ═══════════════════════════════════════════════════════════
def force_scrape(
    db: Session,
    slug: str,
    source: Optional[str] = None,
) -> dict:
    """
    Paksa scrape anime (dipakai endpoint POST /share/empty/{slug}).
    """
    source = (source or settings.default_source).lower()

    try:
        result = scrape_anime(
            path_or_url=f"/anime/{slug}",
            source=source,
            follow_all=True,
            resolve=False,
            filter_dead=False,
        )
    except Exception as e:
        raise ScrapeError(
            f"Gagal scrape '{slug}': {str(e)[:200]}",
            details={"slug": slug, "error": str(e)[:200]},
        )

    counters = save_scrape_result(result)
    return counters