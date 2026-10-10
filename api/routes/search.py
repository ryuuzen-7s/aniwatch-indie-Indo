"""
api/routes/search.py — Endpoint pencarian.
"""
import re
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models.search import SearchResponse, build_search_item
from api.models.common import success_response
from api.services.search_service import (
    search_hybrid,
    trigger_agent_worker,
    get_scrape_status,
    list_scrape_jobs,
    wait_for_scrape,          # ← untuk ?wait=true
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["search"])


# ═══════════════════════════════════════════════════════════
#  GET /share/query?q={keyword}
# ═══════════════════════════════════════════════════════════
@router.get(
    "/query",
    summary="Cari anime",
    description=(
        "Cari anime berdasarkan kata kunci. "
        "Kalau kosong, trigger agent worker di background."
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
    """
    Cari anime.

    - **q**: kata kunci (min 2 karakter)
    - **limit**: max hasil (default 20, max 100)
    - **live**: kalau `false`, hanya cari di DB
    - **wait**: kalau `true`, tunggu scraping selesai (max 60s)
    """
    t0 = time.time()

    # ─── 1. Cari di DB + live scrape ───
    results, from_cache = search_hybrid(
        db, q, source=source, limit=limit, allow_live=live,
    )

    # Build items
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
                "type": "",
                "status": "",
                "total_episode": None,
                "genres": [],
            })

    # ─── 2. Kalau hasil KOSONG → 404 + trigger worker ───
    if not items:
        logger.info(f"[Search] Kosong: '{q}' → trigger agent worker")

        scrape_info = {
            "triggered": False,
            "slug": None,
            "status": "no_slug",
            "message": "Tidak ada slug untuk di-scrape",
        }

        # Cari slug dari berbagai sumber
        slug_candidate = None

        # 1. Dari live scrape result (dict)
        if live and results:
            first = results[0]
            if isinstance(first, dict):
                slug_candidate = first.get("slug")

        # 2. Fallback: dari query
        if not slug_candidate:
            guess = q.lower().strip().replace(" ", "-")
            guess = re.sub(r"[^a-z0-9-]", "", guess)
            if guess and len(guess) >= 3:
                slug_candidate = f"{guess}-sub-indo"
                logger.info(f"[Search] Fallback slug dari query: {slug_candidate}")

        # 3. Trigger agent
        if slug_candidate:
            scrape_info = trigger_agent_worker(
                slug_candidate,
                source=source or "otakudesu",
            )

        # ─── 2b. Kalau wait=true, tunggu scraping selesai ───
        if wait and scrape_info.get("triggered"):
            logger.info(f"[Search] Menunggu scrape '{slug_candidate}' selesai...")
            if wait_for_scrape(timeout=60):
                # Re-search setelah scraping selesai
                logger.info(f"[Search] Scrape selesai, re-search '{q}'")
                new_results, new_from_cache = search_hybrid(
                    db, q, source=source, limit=limit, allow_live=False,
                )
                new_items = []
                for r in new_results:
                    if hasattr(r, "id"):
                        new_items.append(build_search_item(r).model_dump())
                    else:
                        new_items.append({
                            "id": None,
                            "source": source or "otakudesu",
                            "slug": r.get("slug"),
                            "title": r.get("title"),
                            "title_jp": "",
                            "poster_url": r.get("poster_url", ""),
                            "studio": "",
                            "type": "",
                            "status": "",
                            "total_episode": None,
                            "genres": [],
                        })

                if new_items:
                    data = SearchResponse(
                        query=q,
                        source=source,
                        results=new_items,
                        total=len(new_items),
                        from_cache=new_from_cache,
                    )
                    duration_ms = int((time.time() - t0) * 1000)
                    return success_response(
                        data=data.model_dump(),
                        cached=new_from_cache,
                        source="db" if new_from_cache else "live",
                        duration_ms=duration_ms,
                    )

        duration_ms = int((time.time() - t0) * 1000)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SEARCH_EMPTY",
                "message": f"Tidak ada hasil untuk '{q}'",
                "query": q,
                "source": source or "otakudesu",
                "suggestion": (
                    "Data sedang di-scrape otomatis. "
                    "Coba lagi dalam 30 detik."
                ),
                "agent": {
                    **scrape_info,
                    "poll_url": (
                        f"/share/scrape-status/{scrape_info['slug']}"
                        if scrape_info.get("slug") else None
                    ),
                    "retry_after": 30,
                },
                "duration_ms": duration_ms,
            },
        )

    # ─── 3. Ada hasil → return normal ───
    data = SearchResponse(
        query=q,
        source=source,
        results=items,
        total=len(items),
        from_cache=from_cache,
    )

    duration_ms = int((time.time() - t0) * 1000)
    return success_response(
        data=data.model_dump(),
        cached=from_cache,
        source="db" if from_cache else "live",
        duration_ms=duration_ms,
    )


# ═══════════════════════════════════════════════════════════
#  GET /share/scrape-status/{slug}
# ═══════════════════════════════════════════════════════════
@router.get(
    "/scrape-status/{slug}",
    summary="Cek status scrape job",
    description="Cek apakah agent worker sudah selesai scrape anime ini.",
)
async def scrape_status_endpoint(slug: str):
    """Cek status scrape job."""
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
    description="List semua agent worker yang sedang/sudah jalan.",
)
async def scrape_jobs_endpoint():
    """List semua scrape job."""
    return success_response(
        data=list_scrape_jobs(),
        cached=False,
        source="memory",
    )