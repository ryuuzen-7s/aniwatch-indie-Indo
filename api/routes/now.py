"""
api/routes/now.py — Endpoint episode terbaru (Paginated).
"""
import logging
import time
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models.now import NowResponse, NowAnimeItem
from api.models.common import paginated_response
from api.services.now_service import get_now_ongoing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["now"])


@router.get(
    "/now",
    summary="Anime episode terbaru (Paginated)",
    description="Anime ongoing yang baru di-update. Maksimal 10 per halaman.",
)
async def get_now_endpoint(
    page: int = Query(1, ge=1, description="Halaman ke-berapa"),
    limit: int = Query(10, ge=1, le=10, description="Max 10 per halaman"),
    db: Session = Depends(get_db),
):
    """
    Anime ongoing terbaru.
    - **page**: Halaman (default: 1)
    - **limit**: Max 10 (default: 10)
    """
    t0 = time.time()

    # Ambil semua data ongoing (misal limit 100 di level service)
    # Lalu kita potong di sini sesuai pagination.
    # (Jika `get_now_ongoing` bisa menerima limit/offset, lebih baik modifikasi fungsi service-nya).
    
    rows_all = get_now_ongoing(db, limit=100) # Ambil top 100
    total_data = len(rows_all)
    
    offset = (page - 1) * limit
    rows = rows_all[offset : offset + limit]

    # ─── Build items ───
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

    duration_ms = int((time.time() - t0) * 1000)

    response_data = paginated_response(
        items=[item.model_dump() for item in items],
        total=total_data,
        page=page,
        per_page=limit,
        cached=True,
    )

    return response_data