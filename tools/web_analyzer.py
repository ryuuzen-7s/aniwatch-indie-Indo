"""
Web Analyzer — bedah struktur HTML target untuk keperluan scraping.

Fitur:
  - Fetch halaman & simpan HTML mentah
  - Deteksi kandidat selector untuk: title, sinopsis, info, episode, stream, download
  - Klasifikasi link penting (episode, anime, download, external)
  - Deteksi teknologi (CMS, framework, CDN)
  - Cari kata kunci tertentu di HTML
  - Ekspor laporan ke data/log/web/

Usage:
  python -m tools.web_analyzer <URL> [--keyword KATA] [--save-html]
  python -m tools.web_analyzer https://otakudesu.blog/anime/kikansha-mahou-tokubetsu-s2-sub-indo/
"""
import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

from config import config
from logger import get_logger

log = get_logger("WebAnalyzer")

OUTPUT_DIR = config.LOG_DIR / "web"

# Kata kunci yang biasanya menandai bagian penting di situs anime
KEYWORD_HINTS = {
    "title":    ["post-title", "entry-title", "anime-title", "judul"],
    "synopsis": ["sinop", "sinopsis", "synopsis", "description"],
    "info":     ["infozingle", "info-content", "anime-info", "detail"],
    "episode":  ["episodelist", "episode-list", "eps"],
    "stream":   ["mirrorstream", "responsive-embed", "player", "iframe"],
    "download": ["download", "batch", "link-download"],
}

# Tanda teknologi yang mungkin dipakai
TECH_SIGNATURES = {
    "WordPress":    ["wp-content", "wp-includes", "wp-json"],
    "Cloudflare":   ["cloudflare", "__cfduid", "cf-ray"],
    "Blogger":      ["blogspot", "blogger.com"],
    "jQuery":       ["jquery"],
    "Bootstrap":    ["bootstrap"],
    "Font Awesome": ["font-awesome", "fontawesome"],
}


# ======================================================================
# Fetch
# ======================================================================
def fetch_page(url: str) -> tuple[str, requests.Response]:
    """Ambil HTML mentah + response object."""
    log.info(f"Fetch: {url}")
    headers = {
        "User-Agent": config.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    log.info(f"OK {resp.status_code} — {len(resp.text):,} bytes")
    return resp.text, resp


# ======================================================================
# Analisis
# ======================================================================
def analyze_basic(soup: BeautifulSoup, resp: requests.Response) -> dict:
    """Info dasar halaman."""
    title = soup.title.get_text(strip=True) if soup.title else ""
    metas = {}
    for m in soup.find_all("meta"):
        name = m.get("name") or m.get("property")
        content = m.get("content")
        if name and content:
            metas[name] = content[:200]

    headings = [
        {"tag": h.name, "text": h.get_text(strip=True)[:120]}
        for h in soup.find_all(["h1", "h2", "h3"])
    ]

    return {
        "url": resp.url,
        "status_code": resp.status_code,
        "title": title,
        "headings": headings,
        "meta": metas,
        "server": resp.headers.get("Server", ""),
        "content_type": resp.headers.get("Content-Type", ""),
    }


def detect_tech(html: str) -> list[str]:
    """Deteksi teknologi dari signature di HTML."""
    found = []
    low = html.lower()
    for tech, sigs in TECH_SIGNATURES.items():
        if any(sig in low for sig in sigs):
            found.append(tech)
    return found


def find_candidate_selectors(soup: BeautifulSoup) -> dict:
    """
    Cari kandidat selector untuk tiap bagian penting.
    Strategi: cari tag yang class/id-nya mengandung kata kunci.
    """
    candidates: dict[str, list[dict]] = {k: [] for k in KEYWORD_HINTS}

    for tag in soup.find_all(True):
        if not isinstance(tag, Tag):
            continue
        attrs = " ".join(filter(None, [
            " ".join(tag.get("class", [])),
            tag.get("id", ""),
        ])).lower()

        for section, keywords in KEYWORD_HINTS.items():
            for kw in keywords:
                if kw in attrs:
                    candidates[section].append({
                        "tag": tag.name,
                        "class": tag.get("class", []),
                        "id": tag.get("id", ""),
                        "selector": build_selector(tag),
                        "preview": tag.get_text(" ", strip=True)[:120],
                    })
                    break  # cukup 1 match per tag per section

    # Dedup berdasarkan selector
    for section in candidates:
        seen = set()
        unique = []
        for c in candidates[section]:
            if c["selector"] not in seen:
                seen.add(c["selector"])
                unique.append(c)
        candidates[section] = unique[:10]

    return candidates


def build_selector(tag: Tag) -> str:
    """Bangun selector CSS sederhana dari sebuah tag."""
    if tag.get("id"):
        return f"{tag.name}#{tag['id']}"
    if tag.get("class"):
        return f"{tag.name}." + ".".join(tag["class"])
    return tag.name


def detect_links(soup: BeautifulSoup) -> dict:
    """Klasifikasi link penting."""
    result = {"episode": [], "anime": [], "external": [], "download": []}

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)

        if "/episode/" in href:
            result["episode"].append({"text": text, "href": href})
        elif "/anime/" in href:
            result["anime"].append({"text": text, "href": href})
        elif any(x in href.lower() for x in
                 ["download", "mega", "drive", "zippy", "acefile"]):
            result["download"].append({"text": text, "href": href})
        elif href.startswith("http"):
            result["external"].append({"text": text, "href": href})

    for k in result:
        result[k] = result[k][:20]
    return result


def search_keyword(html: str, keyword: str) -> list[dict]:
    """Cari kemunculan keyword di HTML, kembalikan konteksnya."""
    results = []
    low = html.lower()
    kw = keyword.lower()
    start = 0
    while len(results) < 20:
        idx = low.find(kw, start)
        if idx == -1:
            break
        snippet = html[max(0, idx - 100): idx + len(keyword) + 100]
        results.append({"pos": idx, "snippet": snippet.replace("\n", " ").strip()})
        start = idx + len(kw)
    return results


def count_common_classes(soup: BeautifulSoup, top_n: int = 20) -> list[dict]:
    """Hitung class yang paling sering muncul."""
    counter = Counter()
    for tag in soup.find_all(True):
        for cls in tag.get("class", []):
            counter[cls] += 1
    return [{"class": c, "count": n} for c, n in counter.most_common(top_n)]


# ======================================================================
# Output
# ======================================================================
def save_outputs(
    url: str,
    html: str,
    report: dict,
    save_html: bool = False,
) -> Path:
    """Simpan laporan JSON + opsional HTML snapshot ke data/log/web/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    slug = urlparse(url).path.strip("/").replace("/", "_") or "home"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = OUTPUT_DIR / f"{slug}_{ts}"

    report_path = base.with_suffix(".json")
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info(f"Laporan disimpan: {report_path}")

    if save_html:
        html_path = base.with_suffix(".html")
        html_path.write_text(html, encoding="utf-8")
        log.info(f"HTML snapshot: {html_path}")

    return report_path


def print_summary(report: dict, saved_path: Path) -> None:
    """Cetak ringkasan singkat ke console."""
    target = report["basic"]["url"]
    json_name = saved_path.name
    try:
        directory = saved_path.parent.relative_to(config.ROOT_DIR)
    except ValueError:
        directory = saved_path.parent

    sel = report["selectors"]
    links = report["links"]

    print()
    print("=" * 40)
    print("web analyzer")
    print("=" * 40)

    print("target:")
    print(f"  {target}")

    print("=" * 40)
    print("ditemukan")
    print(f"  {len(sel.get('title', []))} kandidat title")
    print(f"  {len(sel.get('synopsis', []))} kandidat sinopsis")
    print(f"  {len(sel.get('info', []))} kandidat info")
    print(f"  {len(sel.get('episode', []))} kandidat episode")
    print(f"  {len(sel.get('stream', []))} kandidat stream")
    print(f"  {len(sel.get('download', []))} kandidat download")
    print(f"  {len(links['episode'])} link episode")
    print(f"  {len(links['download'])} link download")
    print(f"  tech: {', '.join(report['tech']) or '-'}")

    print("=" * 40)
    print(f"{json_name} tersimpan di {directory}")
    print()


# ======================================================================
# Main
# ======================================================================
def analyze(url: str, keyword: str | None = None, save_html: bool = False) -> dict:
    html, resp = fetch_page(url)
    soup = BeautifulSoup(html, "lxml")

    report = {
        "generated_at": datetime.now().isoformat(),
        "basic": analyze_basic(soup, resp),
        "tech": detect_tech(html),
        "selectors": find_candidate_selectors(soup),
        "links": detect_links(soup),
        "common_classes": count_common_classes(soup),
    }

    if keyword:
        report["keyword_search"] = {
            "keyword": keyword,
            "matches": search_keyword(html, keyword),
        }

    saved_path = save_outputs(url, html, report, save_html=save_html)
    print_summary(report, saved_path)
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Bedah struktur HTML target untuk scraping."
    )
    parser.add_argument("url", help="URL halaman yang akan dianalisis")
    parser.add_argument("--keyword", "-k", help="Cari kata kunci di HTML")
    parser.add_argument(
        "--save-html", action="store_true", help="Simpan snapshot HTML mentah"
    )
    args = parser.parse_args()

    try:
        analyze(args.url, keyword=args.keyword, save_html=args.save_html)
    except requests.RequestException as e:
        log.error(f"Gagal fetch: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()