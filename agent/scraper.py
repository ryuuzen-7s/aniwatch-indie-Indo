"""
agent/scraper.py - Core: scrape 1 anime & simpan ke DB.
"""
import sys
import time
import logging
from pathlib import Path
from typing import Optional

# Path fix: import dari root project
ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.repository import save_scrape_result, AnimeRepository
from db import get_session
from core.pipeline import scrape_anime


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  CHECK EXISTING
# ═══════════════════════════════════════════════════════════
def is_in_db(slug: str) -> bool:
    """Cek apakah anime sudah ada di DB."""
    try:
        with get_session() as s:
            anime = AnimeRepository.get_by_slug(s, slug)
            return bool(anime and anime.title)
    except Exception as e:
        logger.warning(f"Check DB error: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#  SCRAPE ONE
# ═══════════════════════════════════════════════════════════
def scrape_one(
    slug: str,
    follow_all: bool = False,
    skip_existing: bool = True,
) -> dict:
    """
    Scrape 1 anime.

    Returns:
        {
            "slug": str,
            "status": "ok" | "skip" | "fail",
            "counters": dict | None,
            "error": str | None,
            "duration": float,
        }
    """
    result = {
        "slug": slug,
        "status": "fail",
        "counters": None,
        "error": None,
        "duration": 0.0,
    }

    t0 = time.time()

    # Skip kalau sudah ada
    if skip_existing and is_in_db(slug):
        result["status"] = "skip"
        result["error"] = "Sudah ada di DB"
        result["duration"] = time.time() - t0
        return result

    # Scrape
    try:
        data = scrape_anime(
            path_or_url=f"/anime/{slug}",
            source="otakudesu",
            follow_all=follow_all,
            resolve=False,
            filter_dead=False,
        )

        # Validasi
        if not data.get("metadata", {}).get("title"):
            raise ValueError("Hasil scrape kosong (metadata.title kosong)")

        counters = save_scrape_result(data)
        result["status"] = "ok"
        result["counters"] = counters

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        logger.error(f"Scrape '{slug}' gagal: {result['error']}")

    result["duration"] = time.time() - t0
    return result