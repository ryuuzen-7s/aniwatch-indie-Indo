"""api/routes/empty.py - Endpoint POST empty (force scrape)."""
import logging
import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config import settings
from api.deps import get_db
from api.models.empty import EmptyRequest, EmptyResponse
from api.models.common import success_response
from api.services.anime_service import force_scrape


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["empty"])


@router.post(
    "/empty/{slug}",
    summary="Paksa scrape anime",
    description="Paksa scrape anime dari source.",
)
async def post_empty_endpoint(
    slug: str,
    body: EmptyRequest = None,
    db: Session = Depends(get_db),
):
    t0 = time.time()

    if body is None:
        body = EmptyRequest()

    source = (body.source or settings.default_source).lower()

    try:
        counters = force_scrape(db, slug, source=source)
        scraped = True
        message = "Scrape berhasil"
    except Exception as e:
        logger.error(f"Force scrape gagal: {e}")
        counters = {"anime": 0, "episodes": 0, "downloads": 0}
        scraped = False
        message = "Scrape gagal: " + str(e)[:200]

    data = EmptyResponse(
        slug=slug,
        source=source,
        scraped=scraped,
        anime=counters.get("anime", 0),
        episodes=counters.get("episodes", 0),
        downloads=counters.get("downloads", 0),
        message=message,
    )

    duration_ms = int((time.time() - t0) * 1000)
    return success_response(
        data=data.model_dump(),
        cached=False,
        source="live" if scraped else "error",
        duration_ms=duration_ms,
    )
