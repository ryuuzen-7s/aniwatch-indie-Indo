"""
api/routes/poster.py — Endpoint poster anime.
"""
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models.poster import PosterResponse
from api.models.common import success_response
from api.services.poster_service import get_poster


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["poster"])


@router.get(
    "/posterid/{slug}",
    summary="Ambil poster anime",
    description="Return URL poster. Pakai `?redirect=true` untuk langsung redirect ke gambar.",
)
async def get_poster_endpoint(
    slug: str,
    source: Optional[str] = Query(None, description="Source provider"),
    redirect: bool = Query(False, description="Redirect langsung ke gambar"),
    db: Session = Depends(get_db),
):
    """
    Poster anime.

    - **slug**: slug anime
    - **redirect**: `true` → HTTP 302 ke gambar langsung
    """
    t0 = time.time()

    anime, poster_url = get_poster(db, slug, source=source)

    if redirect and poster_url:
        return RedirectResponse(url=poster_url, status_code=302)

    data = PosterResponse(
        slug=anime.slug,
        title=anime.title or None,
        poster_url=poster_url,
    )

    duration_ms = int((time.time() - t0) * 1000)
    return success_response(
        data=data.model_dump(),
        cached=True,
        source="db",
        duration_ms=duration_ms,
    )