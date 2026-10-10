"""
api/services/now_service.py — Episode terbaru (Ongoing di DB).
"""
import logging
from typing import List, Tuple

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from db.models import Anime, Episode


logger = logging.getLogger(__name__)


def get_now_ongoing(
    db: Session,
    limit: int = 20,
) -> List[Tuple[Anime, int, int]]:
    """
    Ambil anime ongoing terbaru dari DB.

    Returns:
        [(anime, episode_count, latest_episode_number), ...]
    """
    # Ambil anime dengan status Ongoing
    stmt = (
        select(Anime)
        .where(func.lower(Anime.status).like("%ongoing%"))
        .order_by(Anime.updated_at.desc())
        .limit(limit)
    )
    animes = list(db.execute(stmt).scalars())

    result = []
    for anime in animes:
        # Hitung episode
        ep_count = db.scalar(
            select(func.count()).select_from(Episode)
            .where(Episode.anime_id == anime.id)
        ) or 0

        # Episode terbaru (max episode_number)
        latest = db.scalar(
            select(func.max(Episode.episode_number))
            .where(Episode.anime_id == anime.id)
        )

        result.append((anime, ep_count, latest))

    return result