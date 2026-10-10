"""
api/services/report_service.py — Report link error & linkask.
"""
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from db.models import Anime, Episode, DownloadLink, Report
from db.repository import ReportRepository
from api.exceptions import AnimeNotFoundError
from api.services.anime_service import get_anime


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  REPORT ERROR
# ═══════════════════════════════════════════════════════════
def report_error(
    db: Session,
    slug: str,
    url: Optional[str],
    reason: str,
    quality: Optional[str] = None,
    host: Optional[str] = None,
    reporter_ip: str = "",
) -> Report:
    """Simpan report link error."""
    # Gabung reason + quality + host
    full_reason = reason
    if quality:
        full_reason = f"[{quality}] {full_reason}"
    if host:
        full_reason = f"[{host}] {full_reason}"

    report = ReportRepository.create(db, {
        "slug": slug,
        "type": "error",
        "url": url or "",
        "reason": full_reason[:500],
        "reporter_ip": reporter_ip,
    })

    logger.info(f"📮 Report dari {slug}: {reason[:60]}")
    return report


# ═══════════════════════════════════════════════════════════
#  LINKASK — Cek ketersediaan link
# ═══════════════════════════════════════════════════════════
def ask_link(
    db: Session,
    slug: str,
    type_: str = "all",
    deep: bool = False,
) -> dict:
    """
    Cek apakah anime punya link di DB.
    """
    # Pastikan anime ada
    anime, _ = get_anime(db, slug, refresh=False)

    # Ambil semua episode
    episodes = list(db.execute(
        select(Episode).where(Episode.anime_id == anime.id)
    ).scalars())

    ep_ids = [ep.id for ep in episodes]

    # Stream count (dari field episode.stream_url)
    stream_count = sum(1 for ep in episodes if ep.stream_url)

    # Download count
    download_count = 0
    alive_count = 0
    dead_count = 0

    if ep_ids:
        rows = db.execute(
            select(DownloadLink).where(DownloadLink.episode_id.in_(ep_ids))
        ).scalars()
        for dl in rows:
            download_count += 1
            if dl.is_alive:
                alive_count += 1
            else:
                dead_count += 1

    # Filter berdasarkan type
    has_link = False
    if type_ == "stream":
        has_link = stream_count > 0
    elif type_ == "download":
        has_link = alive_count > 0
    else:  # all
        has_link = stream_count > 0 or alive_count > 0

    result = {
        "slug": slug,
        "has_link": has_link,
        "stream_count": stream_count,
        "download_count": download_count,
        "alive_count": alive_count,
        "dead_count": dead_count,
        "checked_deep": False,
    }

    # Deep check (opsional): resolve shortener
    if deep:
        from core.resolver import resolve_and_check
        # Nanti kalau resolver.py siap
        # Sementara skip dulu
        logger.warning("Deep check belum diimplementasikan")
        result["checked_deep"] = False

    return result