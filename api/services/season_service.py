"""
api/services/season_service.py — Query anime per season (DB-based).
"""
import logging
from datetime import datetime
from typing import Optional, List, Tuple

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from db.models import Anime


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  SEASON → BULAN
# ═══════════════════════════════════════════════════════════
SEASON_MONTHS = {
    "winter": ["jan", "feb", "mar", "januari", "februari", "maret"],
    "spring": ["apr", "may", "jun", "april", "mei", "juni"],
    "summer": ["jul", "aug", "sep", "juli", "agustus", "september"],
    "fall":   ["oct", "nov", "dec", "okt", "november", "desember"],
    # Alternatif
    "autumn": ["oct", "nov", "dec", "okt", "november", "desember"],
}


def parse_season(season_str: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Parse 'fall-2026' atau '2026' → (nama_season, tahun).
    Return (None, None) kalau format tidak valid.
    """
    season_str = season_str.lower().strip()

    # Format: fall-2026, winter-2025
    if "-" in season_str:
        parts = season_str.split("-")
        if len(parts) == 2:
            name, year = parts
            try:
                return name, int(year)
            except ValueError:
                pass

    # Format: 2026 (tahun saja)
    try:
        year = int(season_str)
        return None, year
    except ValueError:
        pass

    return None, None


# ═══════════════════════════════════════════════════════════
#  SEARCH BY SEASON
# ═══════════════════════════════════════════════════════════
def get_anime_by_season(
    db: Session,
    season_str: str,
    limit: int = 50,
) -> List[Anime]:
    """
    Cari anime berdasarkan season di DB.
    Filter berdasarkan `release_date` (string match bulan).
    """
    name, year = parse_season(season_str)

    if not name and not year:
        return []

    stmt = select(Anime)

    # Filter tahun (match di release_date string)
    if year:
        stmt = stmt.where(Anime.release_date.like(f"%{year}%"))

    # Filter bulan sesuai season
    if name:
        months = SEASON_MONTHS.get(name, [])
        if months:
            # OR: release_date LIKE %jan% OR %feb% OR ...
            from sqlalchemy import or_
            conditions = [Anime.release_date.ilike(f"%{m}%") for m in months]
            stmt = stmt.where(or_(*conditions))

    stmt = stmt.order_by(Anime.updated_at.desc()).limit(limit)

    return list(db.execute(stmt).scalars())