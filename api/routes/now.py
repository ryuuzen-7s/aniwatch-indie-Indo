"""
api/routes/now.py — Endpoint episode terbaru & jadwal harian.
"""
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models.now import NowAnimeItem
from api.models.common import paginated_response
from api.services.now_service import get_now_ongoing, get_anime_by_day

logger = logging.getLogger(__name__)

# Variabel router ini yang dicari oleh __init__.py
router = APIRouter(prefix="/share", tags=["now"])


@router.get("/now", summary="Anime episode terbaru (Update)")
async def get_now_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=10),
    db: Session = Depends(get_db),
):
    t0 = time.time()

    rows_all = get_now_ongoing(db, limit=100) 
    total_data = len(rows_all)
    
    offset = (page - 1) * limit
    rows = rows_all[offset : offset + limit]

    items = []
    for anime, ep_count, latest_ep in rows:
        items.append(NowAnimeItem(
            id=anime.id,
            slug=anime.slug,
            title=anime.title or "",
            poster_url=anime.poster_url or "",
            studio=anime.studio or "",
            status=anime.status or "",
            total_episode=anime.total_episode,
            episode_count=ep_count,
            latest_episode_number=latest_ep,
            broadcast_day=anime.broadcast_day or "",
            updated_at=anime.updated_at.isoformat() if anime.updated_at else None,
            genres=anime.genres or [],
        ))

    response_data = paginated_response(
        items=[item.model_dump() for item in items],
        total=total_data,
        page=page,
        per_page=limit,
        cached=True,
    )

    return response_data


@router.get("/day/{hari}", summary="Jadwal anime berdasarkan hari")
async def get_day_endpoint(
    hari: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=10),
    db: Session = Depends(get_db),
):
    t0 = time.time()

    hari_valid = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]
    if hari.lower() not in hari_valid:
        raise HTTPException(
            status_code=400, 
            detail="Hari tidak valid. Gunakan: senin, selasa, rabu, kamis, jumat, sabtu, minggu."
        )

    rows_all = get_anime_by_day(db, day=hari, limit=100)
    total_data = len(rows_all)
    
    offset = (page - 1) * limit
    rows = rows_all[offset : offset + limit]

    items = []
    for anime, ep_count, latest_ep in rows:
        items.append(NowAnimeItem(
            id=anime.id,
            slug=anime.slug,
            title=anime.title or "",
            poster_url=anime.poster_url or "",
            studio=anime.studio or "",
            status=anime.status or "",
            total_episode=anime.total_episode,
            episode_count=ep_count,
            latest_episode_number=latest_ep,
            broadcast_day=anime.broadcast_day or "",
            updated_at=anime.updated_at.isoformat() if anime.updated_at else None,
            genres=anime.genres or [],
        ))

    response_data = paginated_response(
        items=[item.model_dump() for item in items],
        total=total_data,
        page=page,
        per_page=limit,
        cached=True,
    )
    
    response_data["data"]["hari"] = hari.capitalize()

    return response_data