"""
api/routes/anime.py — Endpoint anime.
"""
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_db, common_source
from api.models.anime import (
    AnimeItem, AnimeDetail,
    build_anime_item, build_anime_detail,
)
from api.models.common import success_response
from api.services.anime_service import (
    get_anime, get_episodes, count_episodes,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["anime"])


# ═══════════════════════════════════════════════════════════
#  GET /share/anime/{slug}
# ═══════════════════════════════════════════════════════════
@router.get(
    "/anime/{slug}",
    summary="Detail anime berdasarkan slug",
    description=(
        "Ambil detail anime dari DB. "
        "Kalau tidak ada & belum di-scrape, otomatis scrape dari source."
    ),
)
async def get_anime_endpoint(
    slug: str,
    source: Optional[str] = Query(None, description="Source: otakudesu | kuramanime | animeindo"),
    refresh: bool = Query(False, description="Paksa re-scrape"),
    include_episodes: bool = Query(False, description="Sertakan daftar episode"),
    db: Session = Depends(get_db),
):
    """
    Detail anime.

    - **slug**: slug anime (mis. `yowaki-max-sub-indo`)
    - **source**: source provider (default dari config)
    - **refresh**: paksa re-scrape meski sudah ada di DB
    - **include_episodes**: sertakan daftar episode
    """
    t0 = time.time()

    # Service: get atau scrape
    anime, data_source = get_anime(
        db=db,
        slug=slug,
        source=source,
        refresh=refresh,
    )

    # Build response
    if include_episodes:
        episodes = get_episodes(db, anime.id)
        data = build_anime_detail(anime, episodes)
    else:
        ep_count = count_episodes(db, anime.id)
        data = build_anime_item(anime, episode_count=ep_count)

    duration_ms = int((time.time() - t0) * 1000)

    return success_response(
        data=data.model_dump(),
        cached=(data_source == "db"),
        source=data_source,
        duration_ms=duration_ms,
    )