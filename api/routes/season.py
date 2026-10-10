"""
api/routes/season.py — Endpoint season.
"""
import logging
import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models.season import SeasonResponse, SeasonAnimeItem
from api.models.common import success_response
from api.services.season_service import get_anime_by_season, parse_season, SEASON_MONTHS


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["season"])


@router.get(
    "/season/{season}",
    summary="Anime per season",
    description=(
        "Format: `fall-2026`, `winter-2025`, dll. "
        "Query DB berdasarkan tanggal rilis."
    ),
)
async def get_season_endpoint(
    season: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Anime per season.

    - **season**: `fall-2026`, `winter-2025`, atau `2026` (tahun saja)
    - **limit**: max hasil
    """
    t0 = time.time()

    name, year = parse_season(season)

    animes = get_anime_by_season(db, season, limit=limit)

    items = [
        SeasonAnimeItem(
            id=a.id,
            slug=a.slug,
            title=a.title or "",
            poster_url=a.poster_url or "",
            studio=a.studio or "",
            type=a.type or "",
            status=a.status or "",
            release_date=a.release_date or "",
            genres=a.genres or [],
        )
        for a in animes
    ]

    # Month range
    month_range = None
    if name and name in SEASON_MONTHS:
        months = SEASON_MONTHS[name][:3]  # Ambil 3 singkatan
        month_range = "-".join(m.upper() for m in months)

    data = SeasonResponse(
        season=season,
        year=year,
        month_range=month_range,
        results=items,
        total=len(items),
    )

    duration_ms = int((time.time() - t0) * 1000)
    return success_response(
        data=data.model_dump(),
        cached=True,
        source="db",
        duration_ms=duration_ms,
    )