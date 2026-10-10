"""
core/fetcher.py — HTTP client single-mirror.
"""
import sys
import time
import random
import logging
from pathlib import Path
from typing import Optional, Tuple

# Path fix
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import requests
from bs4 import BeautifulSoup
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type,
)

from config import settings


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  EXCEPTIONS
# ═══════════════════════════════════════════════════════════
class FetchError(Exception):
    """Base fetch error."""
    pass


class AllMirrorsFailedError(FetchError):
    """Fetch gagal (kompatibilitas nama dengan versi lama)."""
    pass


class UnknownSourceError(FetchError):
    """Source tidak dikenal / disabled."""
    pass


# ═══════════════════════════════════════════════════════════
#  BLOCK DETECTION
# ═══════════════════════════════════════════════════════════
BLOCK_KEYWORDS = [
    "just a moment",
    "checking your browser",
    "cf-browser-verification",
    "enable javascript and cookies",
    "access denied",
    "attention required",
    "ddos-guard",
    "server is busy",
    "server busy",
    "please try again later",
    "sedang sibuk",
    "503 service unavailable",
    "502 bad gateway",
]

# Threshold minimum HTML
MIN_VALID_HTML_SIZE = 3000


def is_blocked(html: str, url: str = "") -> bool:
    """
    Cek apakah HTML menandakan blok / error / blank.
    Return True kalau HTML bermasalah.
    """
    if not html:
        return True

    # Cek ukuran
    if len(html) < MIN_VALID_HTML_SIZE:
        return True

    # Cek keyword
    lower = html.lower()
    for kw in BLOCK_KEYWORDS:
        if kw in lower:
            return True

    return False


# ═══════════════════════════════════════════════════════════
#  FETCH SINGLE (dengan retry)
# ═══════════════════════════════════════════════════════════
@retry(
    stop=stop_after_attempt(settings.max_retry),
    wait=wait_exponential(multiplier=settings.retry_backoff, min=1, max=10),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    reraise=True,
)
def _fetch_single(url: str, headers: dict) -> requests.Response:
    return requests.get(
        url,
        headers=headers,
        timeout=settings.request_timeout,
        allow_redirects=True,
    )


# ═══════════════════════════════════════════════════════════
#  PUBLIC: FETCH (single mirror)
# ═══════════════════════════════════════════════════════════
def fetch(
    path: str,
    source: Optional[str] = None,
    parse: bool = True,
    delay: bool = True,
) -> Tuple[Optional[BeautifulSoup], str]:
    """
    Fetch path dari source (single mirror).

    Args:
        path   : "/anime/xxx" atau URL lengkap
        source : "otakudesu" | "kuramanime" | "animeindo"
        parse  : True → return (soup, html)
        delay  : kasih jeda rate limit

    Returns:
        (soup, html) jika parse=True, atau (None, html)

    Raises:
        UnknownSourceError, AllMirrorsFailedError
    """
    source = (source or settings.default_source).lower()
    src = settings.get_source(source)

    if not src:
        raise UnknownSourceError(f"Source '{source}' tidak dikenal")
    if not src.enabled:
        raise UnknownSourceError(f"Source '{source}' disabled")
    if not src.base_url:
        raise UnknownSourceError(f"Source '{source}' tidak punya base_url")

    if delay:
        time.sleep(random.uniform(0.5, settings.rate_limit_delay))

    # Bangun URL
    if path.startswith("http"):
        full_url = path
    else:
        full_url = src.base_url + (path if path.startswith("/") else "/" + path)

    headers = settings.headers_for(source)
    logger.debug(f"[{source}] GET {full_url}")

    try:
        resp = _fetch_single(full_url, headers)
    except requests.Timeout:
        raise AllMirrorsFailedError(f"[{source}] Timeout: {full_url}")
    except requests.ConnectionError as e:
        raise AllMirrorsFailedError(f"[{source}] Koneksi gagal: {str(e)[:100]}")

    logger.info(
        f"[{source}] [{resp.status_code}] {len(resp.content):,} bytes — {full_url}"
    )

    # Cek status HTTP
    if resp.status_code >= 400:
        raise AllMirrorsFailedError(
            f"[{source}] HTTP {resp.status_code} dari {full_url}"
        )

    # Cek blok / blank / server busy
    if is_blocked(resp.text):
        lower = resp.text.lower()
        reason = "HTML blank/kosong"

        if "server is busy" in lower or "server busy" in lower:
            reason = "Server Otakudesu sedang sibuk (soft error)"
        elif "just a moment" in lower:
            reason = "Cloudflare challenge"
        elif "access denied" in lower:
            reason = "Access denied"
        elif len(resp.text) < MIN_VALID_HTML_SIZE:
            reason = f"HTML terlalu pendek ({len(resp.text)} chars)"

        raise AllMirrorsFailedError(f"[{source}] {reason}")

    if parse:
        return BeautifulSoup(resp.text, "lxml"), resp.text
    return None, resp.text


# ═══════════════════════════════════════════════════════════
#  FETCH RAW (untuk link eksternal)
# ═══════════════════════════════════════════════════════════
def fetch_raw(
    url: str,
    timeout: Optional[int] = None,
    stream: bool = True,
    source: Optional[str] = None,
) -> requests.Response:
    """Fetch URL langsung (untuk link eksternal)."""
    headers = settings.headers_for(source) if source else settings.headers.copy()
    return requests.get(
        url,
        headers=headers,
        timeout=timeout or settings.request_timeout,
        allow_redirects=True,
        stream=stream,
    )


# ═══════════════════════════════════════════════════════════
#  HEALTH CHECK
# ═══════════════════════════════════════════════════════════
def check_source(source_name: str) -> dict:
    """Cek status source."""
    src = settings.get_source(source_name)
    if not src:
        return {"name": source_name, "error": "Unknown source", "mirrors": {}}

    result = {"name": source_name, "mirrors": {}}
    headers = settings.headers_for(source_name)

    if not src.base_url:
        result["mirrors"][""] = {"alive": False, "status": 0, "latency_ms": 0,
                                  "error": "base_url kosong"}
        return result

    t0 = time.time()
    try:
        r = requests.get(
            src.base_url,
            headers=headers,
            timeout=8,
            allow_redirects=True,
        )
        latency = int((time.time() - t0) * 1000)
        result["mirrors"][src.base_url] = {
            "alive": r.status_code == 200 and not is_blocked(r.text),
            "status": r.status_code,
            "latency_ms": latency,
        }
    except Exception as e:
        result["mirrors"][src.base_url] = {
            "alive": False,
            "status": 0,
            "latency_ms": 0,
            "error": str(e)[:60],
        }
    return result


def check_all_sources() -> dict:
    return {name: check_source(name) for name in settings.sources.keys()}


# ═══════════════════════════════════════════════════════════
#  TEST
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("=" * 62)
    print("  CHECK ALL SOURCES")
    print("=" * 62)

    if not settings.sources:
        print("⚠️  Tidak ada source di .env")
        sys.exit(1)

    results = check_all_sources()
    for name, r in results.items():
        print(f"\n[{name.upper()}]")
        if "error" in r:
            print(f"  ❌ {r['error']}")
            continue
        for mirror, m in r["mirrors"].items():
            icon = "✅" if m["alive"] else "❌"
            lat = f"{m['latency_ms']}ms" if m["latency_ms"] else "-"
            err = f" ({m.get('error', '')})" if m.get("error") else ""
            print(f"  {icon} [{m['status']:>3}] {lat:>7}  {mirror}{err}")

    print("\n" + "=" * 62)
    print("  TEST FETCH")
    print("=" * 62)

    for source in settings.active_sources.keys():
        print(f"\n[{source.upper()}] /anime/yowaki-max-sub-indo")
        try:
            soup, html = fetch("/anime/yowaki-max-sub-indo", source=source)
            h1 = soup.find("h1") if soup else None
            title = h1.get_text(strip=True) if h1 else "-"
            print(f"  ✅ {len(html):,} chars | {title[:50]}")
        except AllMirrorsFailedError as e:
            print(f"  ❌ {str(e)[:100]}")
        except UnknownSourceError as e:
            print(f"  ⚠️  {e}")
        except Exception as e:
            print(f"  ❌ {type(e).__name__}: {str(e)[:80]}")

    print()