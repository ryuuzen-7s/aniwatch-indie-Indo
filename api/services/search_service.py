"""
api/services/search_service.py — Business logic untuk Search.

Hybrid:
1. Cari di DB dulu (case-insensitive, LIKE)
2. Kalau kosong → scrape Otakudesu search page
"""
import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import quote_plus, urljoin

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from config import settings
from db.models import Anime
from db.repository import AnimeRepository
from core.fetcher import fetch, AllMirrorsFailedError

import threading
from datetime import datetime

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  SEARCH IN DB
# ═══════════════════════════════════════════════════════════
def search_db(
    db: Session,
    query: str,
    limit: int = 20,
) -> List[Anime]:
    """Cari anime di DB (title atau slug atau title_jp)."""
    q = f"%{query.lower()}%"

    stmt = (
        select(Anime)
        .where(
            or_(
                func.lower(Anime.title).like(q),
                func.lower(Anime.slug).like(q),
                func.lower(Anime.title_jp).like(q),
            )
        )
        .order_by(Anime.updated_at.desc())
        .limit(limit)
    )

    return list(db.execute(stmt).scalars())


# ═══════════════════════════════════════════════════════════
#  SEARCH LIVE (scrape Otakudesu)
# ═══════════════════════════════════════════════════════════
def search_live(query: str, source: str = "otakudesu") -> List[dict]:
    """
    Scrape halaman search Otakudesu.
    Return list of dict minimal (belum disimpan ke DB).

    Catatan: Ini hanya return hasil, tidak auto-save ke DB.
    """
    from bs4 import BeautifulSoup

    # URL search Otakudesu: https://otakudesu.blog/?s=keyword
    path = f"/?s={quote_plus(query)}"

    try:
        soup, html = fetch(path, source=source)
    except AllMirrorsFailedError as e:
        logger.warning(f"Search live gagal: {e}")
        return []

    if not soup:
        return []

    results = []

    # Otakudesu search results: cari di .chivsrc li
    for li in soup.select(".chivsrc li"):
        a = li.find("a", href=True)
        if not a:
            continue

        url = a["href"]
        title = a.get_text(strip=True)

        # Skip kalau bukan link anime
        if "/anime/" not in url:
            continue

        # Extract slug
        slug = url.rstrip("/").split("/")[-1]

        # Poster
        img = li.find("img")
        poster = img.get("src") if img else ""

        results.append({
            "slug": slug,
            "title": title,
            "url": url,
            "poster_url": poster,
        })

    logger.info(f"Search live '{query}': {len(results)} hasil")
    return results


# ═══════════════════════════════════════════════════════════
#  HYBRID SEARCH
# ═══════════════════════════════════════════════════════════

def search_hybrid(
    db: Session,
    query: str,
    source: Optional[str] = None,
    limit: int = 20,
    allow_live: bool = True,
) -> Tuple[List, bool]:
    """
    Cari di DB, kalau kosong → live scrape.

    Returns:
        (list_anime_atau_dict, from_cache_bool)
    """
    source = source or settings.default_source

    # 1. DB search
    results = search_db(db, query, limit=limit)
    if results:
        logger.info(f"Search DB '{query}': {len(results)} hasil")
        return results, True

    # 2. Live search (kalau diizinkan)
    if not allow_live:
        return [], False

    logger.info(f"Search DB kosong, coba live scrape...")
    live_results = search_live(query, source=source)

    if not live_results:
        return [], False

    # 3. Return hasil live (belum disimpan ke DB)
    # Convert ke dict sementara
    return live_results, False

# ═══════════════════════════════════════════════════════════
#  TRIGGER AGENT WORKER (BACKGROUND)
# ═══════════════════════════════════════════════════════════



# Tracker untuk mencegah duplikat scrape
_SCRAPE_JOBS: dict[str, dict] = {}
_SCRAPE_LOCK = threading.Lock()


def trigger_agent_worker(slug: str, source: str = "otakudesu") -> dict:
    """
    Trigger agent worker untuk scrape anime di background.

    Args:
        slug   : slug anime yang mau di-scrape
        source : "otakudesu" | "kuramanime" | "animeindo"

    Returns:
        {
            "triggered": bool,
            "slug": str,
            "status": "queued" | "already_running" | "error",
            "message": str,
        }
    """
    from config import settings

    with _SCRAPE_LOCK:
        # Cek apakah sudah ada job jalan
        existing = _SCRAPE_JOBS.get(slug)
        if existing and existing.get("status") == "running":
            return {
                "triggered": False,
                "slug": slug,
                "status": "already_running",
                "message": f"Scrape '{slug}' sedang berjalan",
            }

        # Register job
        _SCRAPE_JOBS[slug] = {
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "source": source,
        }

    # Jalankan di background thread
    def _run_scrape():
        import logging
        logger = logging.getLogger("agent.worker")

        try:
            logger.info(f"[Worker] Mulai scrape: {slug} (source={source})")

            from core.pipeline import scrape_anime
            from db.repository import save_scrape_result

            # Scrape dengan follow_all=True untuk lengkap
            result = scrape_anime(
                path_or_url=f"/anime/{slug}",
                source=source,
                follow_all=True,
                resolve=False,
                filter_dead=False,
            )

            # Validasi
            title = result.get("metadata", {}).get("title", "")
            if not title or title.startswith("Otakudesu - Download"):
                raise ValueError(f"Hasil scrape tidak valid (title='{title[:60]}')")

            # Simpan ke DB
            counters = save_scrape_result(result)

            logger.info(
                f"[Worker] Selesai: {slug} — "
                f"{counters['anime']} anime, {counters['episodes']} ep, "
                f"{counters['downloads']} dl"
            )

            with _SCRAPE_LOCK:
                _SCRAPE_JOBS[slug] = {
                    "status": "done",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "counters": counters,
                }

        except Exception as e:
            import logging
            logger = logging.getLogger("agent.worker")
            logger.error(f"[Worker] Gagal scrape '{slug}': {type(e).__name__}: {e}")

            with _SCRAPE_LOCK:
                _SCRAPE_JOBS[slug] = {
                    "status": "error",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(e)[:200],
                }

    thread = threading.Thread(target=_run_scrape, daemon=True, name=f"scrape-{slug}")
    thread.start()

    return {
        "triggered": True,
        "slug": slug,
        "status": "queued",
        "message": f"Scrape '{slug}' dimulai di background",
    }


def get_scrape_status(slug: str) -> dict:
    """Cek status scrape job."""
    with _SCRAPE_LOCK:
        job = _SCRAPE_JOBS.get(slug)
        if not job:
            return {"slug": slug, "status": "not_found"}
        return {"slug": slug, **job}


def list_scrape_jobs() -> dict:
    """List semua scrape job."""
    with _SCRAPE_LOCK:
        return {
            "total": len(_SCRAPE_JOBS),
            "running": sum(1 for j in _SCRAPE_JOBS.values() if j.get("status") == "running"),
            "jobs": dict(_SCRAPE_JOBS),
        }
