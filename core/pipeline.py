"""
core/pipeline.py — Pipeline scraping untuk API.

Wrapper dari core/extractors.py + logic tambahan.
"""
import logging
import time
from typing import Optional, Callable, Dict, Any

from core.extractors import parse_anime, parse_episode, ParseError
from core.fetcher import AllMirrorsFailedError, UnknownSourceError


logger = logging.getLogger(__name__)


def scrape_anime(
    path_or_url: str,
    source: Optional[str] = None,
    follow_all: bool = True,
    resolve: bool = False,
    filter_dead: bool = False,
    progress: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Scrape anime + episodes.

    Args:
        path_or_url : "/anime/yowaki-max-sub-indo" atau URL lengkap
        source      : "otakudesu" (default dari config)
        follow_all  : True → scrape semua episode, False → hanya pertama
        resolve     : (belum dipakai di versi ini)
        filter_dead : (belum dipakai di versi ini)
        progress    : callback(event, data) optional

    Returns:
        {
            "source": "otakudesu",
            "url": "...",
            "slug": "...",
            "scraped_at": "...",
            "metadata": {...},
            "episodes": [...],
            "episode_details": [...],
        }
    """
    t_start = time.time()

    # ─── 1. Parse halaman anime ───
    logger.debug(f"Parsing anime: {path_or_url}")
    anime_data = parse_anime(path_or_url, source=source)

    # Format hasil (sesuaikan ke format scraper.py lama)
    result = {
        "source": anime_data["source"],
        "url": anime_data["url"],
        "slug": anime_data["slug"],
        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metadata": anime_data["metadata"],
        "episodes": anime_data["episodes"],
        "episode_details": [],
    }

    # ─── 2. Parse episode (kalau follow_all) ───
    episodes_to_scrape = anime_data["episodes"]
    if not follow_all and episodes_to_scrape:
        episodes_to_scrape = episodes_to_scrape[:1]

    logger.info(f"Scraping {len(episodes_to_scrape)} episode...")

    for i, ep in enumerate(episodes_to_scrape, 1):
        logger.debug(f"  [{i}/{len(episodes_to_scrape)}] {ep['title'][:50]}")

        try:
            ep_data = parse_episode(ep["url"], source=source)

            # Sesuaikan dengan format scraper.py
            detail = {
                "url": ep_data["url"],
                "title": ep_data.get("title") or ep["title"],
                "slug": ep_data["slug"],
                "episode_number": ep.get("episode_number"),
                "streams": ep_data.get("streams", []),
                "downloads": ep_data.get("downloads", []),
            }
            result["episode_details"].append(detail)

        except Exception as e:
            logger.warning(f"  ❌ Episode {i} gagal: {e}")
            continue

    # ─── 3. Summary ───
    result["summary"] = {
        "total_episodes": len(anime_data["episodes"]),
        "scraped_episodes": len(result["episode_details"]),
        "total_streams": sum(len(e["streams"]) for e in result["episode_details"]),
        "total_downloads": sum(len(e["downloads"]) for e in result["episode_details"]),
    }

    logger.info(
        f"✅ Scrape selesai ({time.time() - t_start:.2f}s): "
        f"{result['summary']['scraped_episodes']} ep, "
        f"{result['summary']['total_downloads']} dl"
    )

    return result