"""
api/services/now_service.py — Episode terbaru & Jadwal Harian.
"""
import logging
from typing import List, Tuple, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from db.models import Anime, Episode

logger = logging.getLogger(__name__)


def get_now_ongoing(
    db: Session,
    limit: int = 20,
) -> List[Tuple[Anime, int, int]]:
    """
    Ambil anime ongoing terbaru dari DB (berdasarkan updated_at).
    Tidak memfilter hari.
    """
    stmt = (
        select(Anime)
        .where(func.lower(Anime.status).like("%ongoing%"))
        .order_by(Anime.updated_at.desc())
        .limit(limit)
    )
    animes = list(db.execute(stmt).scalars())
    return _build_result(db, animes)


def get_anime_by_day(
    db: Session,
    day: str,
    limit: int = 100,
) -> List[Tuple[Anime, int, int]]:
    """
    Ambil anime berdasarkan Hari Tayang (Senin, Selasa, dll).
    """
    # Menggunakan ilike agar "senin" dan "Senin" sama-sama terbaca
    stmt = (
        select(Anime)
        .where(Anime.broadcast_day.ilike(f"%{day}%"))
        .order_by(Anime.title.asc()) # Urutkan sesuai abjad
        .limit(limit)
    )
    animes = list(db.execute(stmt).scalars())
    return _build_result(db, animes)


def _build_result(db: Session, animes: List[Anime]) -> List[Tuple[Anime, int, int]]:
    """Helper untuk mengambil jumlah episode dan episode terakhir."""
    result = []
    for anime in animes:
        ep_count = db.scalar(
            select(func.count()).select_from(Episode)
            .where(Episode.anime_id == anime.id)
        ) or 0

        latest = db.scalar(
            select(func.max(Episode.episode_number))
            .where(Episode.anime_id == anime.id)
        )
        result.append((anime, ep_count, latest))
    
    return result