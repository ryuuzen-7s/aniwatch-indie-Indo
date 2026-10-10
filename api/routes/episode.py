"""
api/routes/episode.py — Endpoint episode.
"""
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models.episode import (
    EpisodeListResponse, EpisodeDetail,
    build_episode_list_response, build_episode_detail,
)
from api.models.common import success_response
from api.services.episode_service import (
    get_episode_list, get_episode_by_number,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["episode"])


# ═══════════════════════════════════════════════════════════
#  GET /share/episodeid/{slug}
# ═══════════════════════════════════════════════════════════
@router.get(
    "/episodeid/{slug}",
    summary="List semua episode dari anime",
    description="Ambil daftar episode anime berdasarkan slug.",
)
async def get_episode_list_endpoint(
    slug: str,
    source: Optional[str] = Query(None, description="Source provider"),
    db: Session = Depends(get_db),
):
    """List episode berdasarkan anime slug."""
    t0 = time.time()

    anime, episodes_data = get_episode_list(db, slug, source=source)

    data = build_episode_list_response(anime, episodes_data)

    duration_ms = int((time.time() - t0) * 1000)
    return success_response(
        data=data.model_dump(),
        cached=True,
        source="db",
        duration_ms=duration_ms,
    )


# ═══════════════════════════════════════════════════════════
#  GET /share/episode/{number}/{slug}
# ═══════════════════════════════════════════════════════════
@router.get(
    "/episode/{number}/{slug}",
    summary="Detail episode spesifik",
    description=(
        "Ambil detail episode (stream + download) berdasarkan "
        "nomor episode dan anime slug."
    ),
)
async def get_episode_endpoint(
    number: int,
    slug: str,
    source: Optional[str] = Query(None, description="Source provider"),
    include_downloads: bool = Query(True, description="Sertakan link download"),
    db: Session = Depends(get_db),
):
    """
    Detail episode.

    - **number**: nomor episode (mis. `1`)
    - **slug**: slug anime (mis. `yowaki-max-sub-indo`)
    - **include_downloads**: `false` untuk response ringan tanpa download
    """
    t0 = time.time()

    anime, episode, downloads = get_episode_by_number(
        db, anime_slug=slug, episode_number=number, source=source,
    )

    detail = build_episode_detail(
        episode,
        downloads=downloads if include_downloads else [],
        anime=anime,
    )

    duration_ms = int((time.time() - t0) * 1000)
    return success_response(
        data=detail.model_dump(),
        cached=True,
        source="db",
        duration_ms=duration_ms,
    )