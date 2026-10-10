"""
api/services/poster_service.py — Ambil poster anime.
"""
import logging
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from db.models import Anime
from api.services.anime_service import get_anime


logger = logging.getLogger(__name__)


def get_poster(
    db: Session,
    slug: str,
    source: Optional[str] = None,
) -> Tuple[Anime, Optional[str]]:
    """
    Ambil anime + URL poster.
    Return (anime, poster_url).
    """
    anime, _ = get_anime(db, slug, source=source, refresh=False)
    poster_url = anime.poster_url if anime else None
    return anime, poster_url