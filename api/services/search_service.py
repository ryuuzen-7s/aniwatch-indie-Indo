"""
api/services/search_service.py — Business logic untuk Search.

Fitur:
- Hybrid search: DB dulu → live scrape Otakudesu
- Parser Otakudesu yang benar (handle /anime/ dan /episode/)
- Agent worker trigger (background thread)
- Tracking scrape job (status, counters, log)
- Retry & global write lock (cegah database locked)
"""
import re
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from urllib.parse import quote_plus, urlparse

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from config import settings
from db.models import Anime
from db.repository import AnimeRepository, save_scrape_result
from core.fetcher import fetch, AllMirrorsFailedError


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  SCRAPE JOB TRACKING
# ═══════════════════════════════════════════════════════════
_SCRAPE_JOBS: Dict[str, Dict[str, Any]] = {}
_SCRAPE_LOCK = threading.Lock()


def is_scrape_running() -> bool:
    """Cek apakah ada scrape yang sedang jalan."""
    with _SCRAPE_LOCK:
        return any(
            j.get("status") == "running"
            for j in _SCRAPE_JOBS.values()
        )


def wait_for_scrape(timeout: int = 60) -> bool:
    """
    Tunggu sampai tidak ada scrape yang running.

    Args:
        timeout: max detik untuk tunggu

    Returns:
        True kalau scrape selesai, False kalau timeout
    """
    start = time.time()
    while is_scrape_running():
        if time.time() - start > timeout:
            logger.warning(f"[Wait] Timeout {timeout}s, scrape masih jalan")
            return False
        time.sleep(1)
    return True


def get_running_slugs() -> List[str]:
    """List slug yang sedang di-scrape."""
    with _SCRAPE_LOCK:
        return [
            slug for slug, job in _SCRAPE_JOBS.items()
            if job.get("status") == "running"
        ]


# ═══════════════════════════════════════════════════════════
#  SEARCH IN DB
# ═══════════════════════════════════════════════════════════
def search_db(
    db: Session,
    query: str,
    limit: int = 20,
) -> List[Anime]:
    """
    Cari anime di DB berdasarkan title, slug, atau title_jp.
    """
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
#  SEARCH LIVE — OTAKUDESU PARSER
# ═══════════════════════════════════════════════════════════
def search_live(query: str, source: str = "otakudesu") -> List[dict]:
    """
    Scrape halaman search Otakudesu.

    Struktur HTML Otakudesu:
      <h2><a href="/anime/slug-sub-indo/">Title</a></h2>
      atau
      <h2><a href="/episode/slug-episode-1-sub-indo/">Title Episode 1</a></h2>

    Return:
        List of dict {slug, title, url, poster_url, type}
    """
    path = f"/?s={quote_plus(query)}"

    try:
        soup, html = fetch(path, source=source)
    except AllMirrorsFailedError as e:
        logger.warning(f"[Search Live] Gagal fetch: {e}")
        return []
    except Exception as e:
        logger.error(f"[Search Live] Error: {e}")
        return []

    if not soup:
        logger.warning(f"[Search Live] Response kosong: {query}")
        return []

    results: List[dict] = []
    seen_slugs: set = set()

    # ─── Strategi 1: Cari semua <h2><a> ───
    for h2 in soup.find_all("h2"):
        a = h2.find("a", href=True)
        if not a:
            continue

        href = a["href"]
        title = a.get_text(strip=True)

        if not href or not title:
            continue

        # Ekstrak path
        if href.startswith("http"):
            parsed = urlparse(href)
            path_only = parsed.path
        else:
            path_only = href

        # Harus /anime/ atau /episode/
        is_anime = "/anime/" in path_only
        is_episode = "/episode/" in path_only

        if not (is_anime or is_episode):
            continue

        # Ekstrak slug
        slug = path_only.rstrip("/").split("/")[-1]
        if not slug or slug in seen_slugs:
            continue
        seen_slugs.add(slug)

        results.append({
            "slug": slug,
            "title": title,
            "url": href if href.startswith("http") else f"https://otakudesu.blog{href}",
            "poster_url": "",
            "type": "anime" if is_anime else "episode",
        })

    # ─── Strategi 2: Fallback ───
    if not results:
        for a in soup.select(".venz a[href], .chivsrc a[href]"):
            href = a.get("href", "")
            title = a.get_text(strip=True)

            if not href or not title:
                continue

            parsed = urlparse(href) if href.startswith("http") else None
            path_only = parsed.path if parsed else href

            if "/anime/" not in path_only and "/episode/" not in path_only:
                continue

            slug = path_only.rstrip("/").split("/")[-1]
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            results.append({
                "slug": slug,
                "title": title,
                "url": href if href.startswith("http") else f"https://otakudesu.blog{href}",
                "poster_url": "",
                "type": "anime" if "/anime/" in path_only else "episode",
            })

    # ─── Extract parent anime dari episode slug ───
    anime_results = [r for r in results if r["type"] == "anime"]

    if not anime_results and results:
        for r in results:
            slug = r["slug"]
            # Pattern: "xxx-episode-N-sub-indo" → "xxx-sub-indo"
            m = re.match(r"^(.+?)-episode-\d+", slug)
            if m:
                parent_slug = m.group(1) + "-sub-indo"
                if parent_slug not in seen_slugs:
                    seen_slugs.add(parent_slug)
                    parent_title = re.split(r"\s+Episode\s+\d+", r["title"], maxsplit=1)[0]
                    anime_results.append({
                        "slug": parent_slug,
                        "title": parent_title.strip(),
                        "url": f"https://otakudesu.blog/anime/{parent_slug}/",
                        "poster_url": "",
                        "type": "anime",
                        "from_episode": True,
                    })

    logger.info(
        f"[Search Live] '{query}': "
        f"{len(results)} raw, {len(anime_results)} anime"
    )

    return anime_results if anime_results else results


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
        logger.info(f"[Search] DB '{query}': {len(results)} hasil")
        return results, True

    # 2. Live search (kalau diizinkan)
    if not allow_live:
        return [], False

    logger.info(f"[Search] DB kosong, coba live scrape...")
    live_results = search_live(query, source=source)

    if not live_results:
        return [], False

    return live_results, False


# ═══════════════════════════════════════════════════════════
#  AGENT WORKER TRIGGER
# ═══════════════════════════════════════════════════════════
def trigger_agent_worker(slug: str, source: str = "otakudesu") -> dict:
    """
    Trigger agent worker untuk scrape anime di background.

    Returns:
        {triggered, slug, status, message}
    """
    # Cek apakah sudah ada job jalan
    with _SCRAPE_LOCK:
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
            "method": "thread",
        }

    # Jalankan di background thread
    def _run_scrape():
        try:
            logger.info(f"[Worker] Mulai scrape: {slug} (source={source})")

            from core.pipeline import scrape_anime

            counters = None
            last_error = None
            max_retries = 3

            for attempt in range(max_retries):
                try:
                    result = scrape_anime(
                        path_or_url=f"/anime/{slug}",
                        source=source,
                        follow_all=True,
                        resolve=False,
                        filter_dead=False,
                    )

                    title = result.get("metadata", {}).get("title", "")
                    if not title or title.startswith("Otakudesu - Download"):
                        raise ValueError(
                            f"Hasil scrape tidak valid (title='{title[:60]}')"
                        )

                    counters = save_scrape_result(result)
                    break

                except OperationalError as e:
                    last_error = e
                    if "database is locked" in str(e).lower():
                        if attempt < max_retries - 1:
                            wait = 1.0 * (attempt + 1)
                            logger.warning(
                                f"[Worker] DB locked, retry {attempt + 1}/{max_retries} "
                                f"in {wait}s"
                            )
                            time.sleep(wait)
                            continue
                    raise
                except (ValueError, Exception):
                    raise

            if counters is None:
                raise last_error or Exception("Scrape gagal tanpa error")

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
            logger.error(f"[Worker] Gagal scrape '{slug}': {type(e).__name__}: {e}")

            with _SCRAPE_LOCK:
                _SCRAPE_JOBS[slug] = {
                    "status": "error",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(e)[:200],
                }

    thread = threading.Thread(
        target=_run_scrape,
        daemon=True,
        name=f"scrape-{slug}",
    )
    thread.start()

    return {
        "triggered": True,
        "slug": slug,
        "status": "queued",
        "message": f"Scrape '{slug}' dimulai di background",
    }


# ═══════════════════════════════════════════════════════════
#  SCRAPE STATUS
# ═══════════════════════════════════════════════════════════
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
        jobs = dict(_SCRAPE_JOBS)
        return {
            "total": len(jobs),
            "running": sum(
                1 for j in jobs.values() if j.get("status") == "running"
            ),
            "done": sum(
                1 for j in jobs.values() if j.get("status") == "done"
            ),
            "error": sum(
                1 for j in jobs.values() if j.get("status") == "error"
            ),
            "jobs": jobs,
        }


def clear_scrape_jobs() -> int:
    """Hapus semua job."""
    with _SCRAPE_LOCK:
        count = len(_SCRAPE_JOBS)
        _SCRAPE_JOBS.clear()
        return count


def cleanup_done_jobs(max_age_hours: int = 24) -> int:
    """Hapus job yang selesai & berumur > max_age_hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    removed = 0

    with _SCRAPE_LOCK:
        keys_to_remove = []
        for slug, job in _SCRAPE_JOBS.items():
            if job.get("status") in ("done", "error"):
                finished_str = job.get("finished_at")
                if finished_str:
                    try:
                        finished = datetime.fromisoformat(finished_str)
                        if finished.tzinfo is None:
                            finished = finished.replace(tzinfo=timezone.utc)
                        if finished < cutoff:
                            keys_to_remove.append(slug)
                    except Exception:
                        pass

        for slug in keys_to_remove:
            del _SCRAPE_JOBS[slug]
            removed += 1

    return removed