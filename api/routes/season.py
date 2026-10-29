"""
api/routes/season.py — Endpoint season dengan pagination (Max 10 per page).
"""
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models.season import SeasonResponse, SeasonAnimeItem
from api.models.common import paginated_response, success_response
from api.services.season_service import (
    get_anime_by_season,
    parse_season,
    SEASON_MONTHS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["season"])


@router.get(
    "/season/{season}",
    summary="Anime per season (Paginated)",
    description="Format: `fall-2026`. Maksimal 10 anime per halaman.",
)
async def get_season_endpoint(
    season: str,
    page: int = Query(1, ge=1, description="Halaman ke-berapa"),
    limit: int = Query(10, ge=1, le=10, description="Max 10 per halaman"),
    db: Session = Depends(get_db),
):
    """
    Anime per season.
    - **season**: `fall-2026`, `winter-2025`, atau `2026`
    - **page**: Halaman (default: 1)
    - **limit**: Max 10 (default: 10)
    """
    t0 = time.time()

    name, year = parse_season(season)

    # 1. Hitung total data (untuk pagination meta)
    # Note: Untuk efisiensi, sebaiknya buat fungsi count di season_service.
    # Di sini kita asumsikan get_anime_by_season bisa menerima offset/limit
    # atau kita ambil semua dulu lalu potong di memori (kurang efisien untuk data besar).
    
    # Kita ambil total dari fungsi service yang sudah ada
    # (Jika service belum mendukung limit/offset, kita potong manual di sini).
    
    # ─── Mock: Ambil semua data season, lalu potong ───
    animes_all = get_anime_by_season(db, season, limit=1000)
    total_data = len(animes_all)
    
    # Hitung offset
    offset = (page - 1) * limit
    animes = animes_all[offset : offset + limit]

    # ─── Build items ───
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

    month_range = None
    if name and name in SEASON_MONTHS:
        months = SEASON_MONTHS[name][:3]
        month_range = "-".join(m.upper() for m in months)

    # Data tambahan untuk metadata
    extra_data = {
        "season": season,
        "year": year,
        "month_range": month_range,
    }

    # Karena menggunakan paginated_response, data utama ada di `items`
    # dan tambahan info ada di `data`.
    duration_ms = int((time.time() - t0) * 1000)
    
    # Build response dengan format pagination
    response_data = paginated_response(
        items=[item.model_dump() for item in items],
        total=total_data,
        page=page,
        per_page=limit,
        cached=True,
    )
    
    # Sisipkan info season ke dalam data
    response_data["data"].update(extra_data)

    return response_data