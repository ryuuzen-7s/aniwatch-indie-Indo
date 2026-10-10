"""
api/routes/now.py — Endpoint episode terbaru.
"""
import logging
import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models.now import NowResponse, NowAnimeItem
from api.models.common import success_response
from api.services.now_service import get_now_ongoing


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["now"])


@router.get(
    "/now",
    summary="Anime episode terbaru (ongoing)",
    description="Anime ongoing yang baru di-update, urut terbaru.",
)
async def get_now_endpoint(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Anime ongoing terbaru dari DB.
    """
    t0 = time.time()

    rows = get_now_ongoing(db, limit=limit)

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
            updated_at=anime.updated_at.isoformat() if anime.updated_at else None,
            genres=anime.genres or [],
        ))

    data = NowResponse(results=items, total=len(items))

    duration_ms = int((time.time() - t0) * 1000)
    return success_response(
        data=data.model_dump(),
        cached=True,
        source="db",
        duration_ms=duration_ms,
    )