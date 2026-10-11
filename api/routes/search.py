"""
api/routes/search.py — Endpoint pencarian.

Flow HTTP Status:
- 200 OK           → data ada di DB
- 202 Accepted     → data sedang di-scrape (Retry-After)
- 204 No Content   → tidak ada & tidak bisa scrape
- 429              → rate limit
"""
import re
import logging
import time
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models.search import SearchResponse, build_search_item
from api.models.common import success_response
from api.services.search_service import (
    search_db,
    search_live,
    search_hybrid,
    trigger_agent_worker,
    get_scrape_status,
    list_scrape_jobs,
    get_running_slugs,
    wait_for_scrape,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["search"])


# ═══════════════════════════════════════════════════════════
#  HELPER
# ═══════════════════════════════════════════════════════════
def _now_iso() -> str:
    """ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _build_items(results: List, source: Optional[str]) -> List[dict]:
    """Build list items dari hasil search (ORM atau dict)."""
    items = []
    for r in results:
        if hasattr(r, "id"):
            items.append(build_search_item(r).model_dump())
        else:
            items.append({
                "id": None,
                "source": source or "otakudesu",
                "slug": r.get("slug"),
                "title": r.get("title"),
                "title_jp": "",
                "poster_url": r.get("poster_url", ""),
                "studio": "",
                "type": r.get("type", ""),
                "status": "",
                "total_episode": None,
                "genres": [],
            })
    return items


def _find_matching_slug(query: str, running_slugs: List[str]) -> Optional[str]:
    """Cari slug yang match dengan query di antara running slugs."""
    if not running_slugs:
        return None

    query_lower = query.lower().strip()
    query_slug = query_lower.replace(" ", "-")

    for slug in running_slugs:
        slug_lower = slug.lower()

        if query_slug in slug_lower:
            return slug

        slug_base = (
            slug_lower
            .replace("-sub-indo", "")
            .replace("-sub-ind", "")
        )
        if slug_base and slug_base in query_slug:
            return slug

    return None


def _build_202_response(
    query: str,
    scrape_info: dict,
    status_label: str,
    retry_after: int,
    duration_ms: int,
) -> JSONResponse:
    """Build response 202 Accepted."""
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "success": True,
            "data": {
                "query": query,
                "status": status_label,
                "message": (
                    f"Data sedang di-scrape. "
                    f"Coba lagi dalam {retry_after} detik."
                ),
                "agent": {
                    **scrape_info,
                    "poll_url": (
                        f"/share/scrape-status/{scrape_info['slug']}"
                        if scrape_info.get("slug") else None
                    ),
                    "retry_after": retry_after,
                },
                "duration_ms": duration_ms,
            },
            "meta": {
                "timestamp": _now_iso(),
            },
            "error": None,
        },
        headers={
            "Retry-After": str(retry_after),
        },
    )


def _build_204_response(query: str, duration_ms: int) -> JSONResponse:
    """Build response 204 No Content."""
    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT,
        content={
            "success": False,
            "data": None,
            "meta": {
                "timestamp": _now_iso(),
            },
            "error": {
                "code": "NO_RESULT",
                "message": f"Tidak ada hasil untuk '{query}'",
                "status": 204,
                "details": {
                    "query": query,
                    "suggestion": "Coba kata kunci lain.",
                },
            },
        },
    )


# ═══════════════════════════════════════════════════════════
#  GET /share/query?q={keyword}
# ═══════════════════════════════════════════════════════════
@router.get(
    "/query",
    summary="Cari anime",
    description=(
        "Cari anime berdasarkan kata kunci.\n\n"
        "**Response:**\n"
        "- `200 OK` — data ada di DB\n"
        "- `202 Accepted` — data sedang di-scrape (`Retry-After` header)\n"
        "- `204 No Content` — tidak ada hasil & tidak bisa scrape"
    ),
)
async def search_endpoint(
    q: str = Query(..., min_length=2, description="Kata kunci pencarian"),
    source: Optional[str] = Query(None, description="Source provider"),
    limit: int = Query(20, ge=1, le=100, description="Max hasil"),
    live: bool = Query(True, description="Izinkan live scrape kalau DB kosong"),
    wait: bool = Query(False, description="Tunggu scraping selesai (max 60s)"),
    db: Session = Depends(get_db),
):
    """Cari anime."""
    t0 = time.time()
    source_name = source or "otakudesu"

    # ─── 1. Cari di DB ───
    db_results = search_db(db, q, limit=limit)

    if db_results:
        items = _build_items(db_results, source)
        data = SearchResponse(
            query=q,
            source=source,
            results=items,
            total=len(items),
            from_cache=True,
        )
        duration_ms = int((time.time() - t0) * 1000)

        logger.info(f"[Search] '{q}' → 200 OK ({len(items)} hasil)")

        return success_response(
            data=data.model_dump(),
            cached=True,
            source="db",
            duration_ms=duration_ms,
        )

    # ─── 2. Cek running scrape ───
    running_slugs = get_running_slugs()
    matching_slug = _find_matching_slug(q, running_slugs)

    if matching_slug:
        logger.info(f"[Search] '{q}' → 202 (already running: {matching_slug})")

        return _build_202_response(
            query=q,
            scrape_info={
                "triggered": False,
                "slug": matching_slug,
                "status": "already_running",
                "message": f"Scrape '{matching_slug}' sedang berjalan",
            },
            status_label="already_processing",
            retry_after=15,
            duration_ms=int((time.time() - t0) * 1000),
        )

    # ─── 3. Cari slug dari live scrape ───
    slug_candidate = None

    if live:
        live_results = search_live(q, source=source_name)
        if live_results:
            first = live_results[0]
            if isinstance(first, dict):
                slug_candidate = first.get("slug")

    # Fallback dari query
    if not slug_candidate:
        guess = q.lower().strip().replace(" ", "-")
        guess = re.sub(r"[^a-z0-9-]", "", guess)
        if guess and len(guess) >= 3:
            slug_candidate = f"{guess}-sub-indo"
            logger.info(f"[Search] Fallback slug: {slug_candidate}")

    # ─── 4. Tidak bisa scrape → 204 ───
    if not slug_candidate:
        logger.info(f"[Search] '{q}' → 204 (no slug)")
        return _build_204_response(
            query=q,
            duration_ms=int((time.time() - t0) * 1000),
        )

    # ─── 5. Trigger agent → 202 ───
    scrape_info = trigger_agent_worker(slug_candidate, source=source_name)
    retry_after = 30 if scrape_info.get("triggered") else 15

    if wait and scrape_info.get("triggered"):
        logger.info(f"[Search] '{q}' menunggu scrape selesai...")

        if wait_for_scrape(timeout=60):
            new_results = search_db(db, q, limit=limit)

            if new_results:
                items = _build_items(new_results, source)
                data = SearchResponse(
                    query=q,
                    source=source,
                    results=items,
                    total=len(items),
                    from_cache=False,
                )
                duration_ms = int((time.time() - t0) * 1000)

                return success_response(
                    data=data.model_dump(),
                    cached=False,
                    source="db",
                    duration_ms=duration_ms,
                )

    logger.info(f"[Search] '{q}' → 202 (triggered: {slug_candidate})")

    return _build_202_response(
        query=q,
        scrape_info=scrape_info,
        status_label=(
            "processing"
            if scrape_info.get("triggered")
            else "already_processing"
        ),
        retry_after=retry_after,
        duration_ms=int((time.time() - t0) * 1000),
    )


# ═══════════════════════════════════════════════════════════
#  GET /share/scrape-status/{slug}
# ═══════════════════════════════════════════════════════════
@router.get(
    "/scrape-status/{slug}",
    summary="Cek status scrape job",
)
async def scrape_status_endpoint(slug: str):
    return success_response(
        data=get_scrape_status(slug),
        cached=False,
        source="memory",
    )


# ═══════════════════════════════════════════════════════════
#  GET /share/scrape-jobs
# ═══════════════════════════════════════════════════════════
@router.get(
    "/scrape-jobs",
    summary="List semua scrape job",
)
async def scrape_jobs_endpoint():
    return success_response(
        data=list_scrape_jobs(),
        cached=False,
        source="memory",
    )