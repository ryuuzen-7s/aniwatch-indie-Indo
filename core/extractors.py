"""
core/extractors.py — Public API untuk parsing HTML.

Contoh:
    from core.extractors import parse_anime, parse_episode
    data = parse_anime("otakudesu", "/anime/yowaki-max-sub-indo")
"""
import logging
from typing import Dict, Any, Optional

from bs4 import BeautifulSoup

from config import settings
from core.fetcher import fetch, AllMirrorsFailedError, UnknownSourceError
from core.sources import get_parser


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  EXCEPTIONS
# ═══════════════════════════════════════════════════════════
class ParserNotFoundError(Exception):
    """Parser untuk source ini belum diimplementasi."""
    pass


class ParseError(Exception):
    """Gagal parsing HTML."""
    pass


# ═══════════════════════════════════════════════════════════
#  HELPER: DAPATKAN PARSER
# ═══════════════════════════════════════════════════════════
def _get_parser(source: str):
    """Ambil instance parser untuk source."""
    parser_cls = get_parser(source)
    if not parser_cls:
        raise ParserNotFoundError(
            f"Parser untuk source '{source}' belum tersedia. "
            f"Source yang supported: cek core/sources/__init__.py"
        )
    src_cfg = settings.get_source(source)
    base_url = src_cfg.base_url if src_cfg else ""
    return parser_cls(base_url=base_url)


# ═══════════════════════════════════════════════════════════
#  PARSE ANIME
# ═══════════════════════════════════════════════════════════
def parse_anime(
    path_or_url: str,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch + parse halaman anime.

    Args:
        path_or_url : "/anime/yowaki-max-sub-indo" atau URL lengkap
        source      : "otakudesu" (default: settings.default_source)

    Returns:
        {
            "source": "otakudesu",
            "url": "...",
            "slug": "yowaki-max-sub-indo",
            "metadata": {...},
            "episodes": [...],
        }
    """
    source = (source or settings.default_source).lower()
    parser = _get_parser(source)

    soup, html = fetch(path_or_url, source=source)
    if not soup:
        raise ParseError(f"Gagal fetch: {path_or_url}")

    # Bangun URL absolut
    full_url = path_or_url
    if not path_or_url.startswith("http"):
        src_cfg = settings.get_source(source)
        base = src_cfg.base_url if src_cfg else ""
        full_url = base + (path_or_url if path_or_url.startswith("/") else "/" + path_or_url)

    try:
        metadata = parser.extract_metadata(soup)
        episodes = parser.extract_episodes(soup)
    except Exception as e:
        logger.error(f"Parse error [{source}]: {e}")
        raise ParseError(f"Gagal parsing {full_url}: {e}")

    return {
        "source": source,
        "url": full_url,
        "slug": parser.slug_from_url(full_url),
        "metadata": metadata,
        "episodes": episodes,
    }


# ═══════════════════════════════════════════════════════════
#  PARSE EPISODE
# ═══════════════════════════════════════════════════════════
def parse_episode(
    path_or_url: str,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch + parse halaman episode (stream + download).

    Args:
        path_or_url : "/episode/ywmx-episode-1-sub-indo/" atau URL lengkap
        source      : "otakudesu"

    Returns:
        {
            "source": "otakudesu",
            "url": "...",
            "slug": "ywmx-episode-1-sub-indo",
            "title": "...",
            "streams": [...],
            "downloads": [...],
            "nav": {...},
        }
    """
    source = (source or settings.default_source).lower()
    parser = _get_parser(source)

    soup, html = fetch(path_or_url, source=source)
    if not soup:
        raise ParseError(f"Gagal fetch: {path_or_url}")

    # URL absolut
    full_url = path_or_url
    if not path_or_url.startswith("http"):
        src_cfg = settings.get_source(source)
        base = src_cfg.base_url if src_cfg else ""
        full_url = base + (path_or_url if path_or_url.startswith("/") else "/" + path_or_url)

    try:
        title_el = soup.find("h1")
        title = parser.clean_text(title_el.get_text()) if title_el else None
        streams = parser.extract_stream(soup)
        downloads = parser.extract_downloads(soup)
        nav = _extract_nav(soup, parser)
    except Exception as e:
        logger.error(f"Parse error [{source}]: {e}")
        raise ParseError(f"Gagal parsing episode {full_url}: {e}")

    return {
        "source": source,
        "url": full_url,
        "slug": parser.slug_from_url(full_url),
        "title": title,
        "streams": streams,
        "downloads": downloads,
        "nav": nav,
    }


# ═══════════════════════════════════════════════════════════
#  NAVIGASI prev/next (khusus Otakudesu)
# ═══════════════════════════════════════════════════════════
def _extract_nav(soup: BeautifulSoup, parser) -> Dict[str, str]:
    """Ekstrak navigasi prev/next dari halaman episode."""
    nav = {}
    for a in soup.select(".prevnext a, .flir a"):
        text = parser.clean_text(a.get_text()).lower()
        href = a.get("href", "")
        if not href:
            continue
        url = parser.normalize_url(href)
        if "prev" in text or "sebelum" in text:
            nav["prev"] = url
        elif "next" in text or "selanjutnya" in text:
            nav["next"] = url
    return nav


# ═══════════════════════════════════════════════════════════
#  QUICK TEST
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    import json
    import logging
    from pathlib import Path

    # Path fix kalau dijalankan langsung
    if __name__ == "__main__" and __package__ is None:
        sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("=" * 62)
    print("  TEST PARSER — OTAKUDESU")
    print("=" * 62)

    # Test parse anime
    print("\n[1] Parse anime: /anime/yowaki-max-sub-indo")
    try:
        data = parse_anime("/anime/yowaki-max-sub-indo", source="otakudesu")
        meta = data["metadata"]
        print(f"    ✅ Source   : {data['source']}")
        print(f"    ✅ Slug     : {data['slug']}")
        print(f"    ✅ Judul    : {meta.get('title', '-')}")
        print(f"    ✅ Studio   : {meta.get('studio', '-')}")
        print(f"    ✅ Status   : {meta.get('status', '-')}")
        print(f"    ✅ Genre    : {', '.join(meta.get('genres', []))}")
        print(f"    ✅ Episode  : {len(data['episodes'])}")
        for ep in data["episodes"][:3]:
            print(f"        - [{ep['episode_number']}] {ep['title'][:50]}")
    except Exception as e:
        print(f"    ❌ {type(e).__name__}: {e}")
        data = None

    # Test parse episode (kalau ada)
    if data and data["episodes"]:
        ep_url = data["episodes"][0]["url"]
        print(f"\n[2] Parse episode: {ep_url}")
        try:
            ep_data = parse_episode(ep_url, source="otakudesu")
            print(f"    ✅ Judul    : {ep_data.get('title', '-')}")
            print(f"    ✅ Stream   : {len(ep_data['streams'])}")
            for s in ep_data["streams"][:2]:
                print(f"        - [{s['host']}] {s['url'][:60]}")
            print(f"    ✅ Download : {len(ep_data['downloads'])}")
            for d in ep_data["downloads"][:5]:
                print(f"        - [{d['quality']:<12}] {d['host']:<12} {d['url'][:50]}")
            if ep_data.get("nav"):
                print(f"    ✅ Nav      : {ep_data['nav']}")
        except Exception as e:
            print(f"    ❌ {type(e).__name__}: {e}")

    print("\n" + "=" * 62)