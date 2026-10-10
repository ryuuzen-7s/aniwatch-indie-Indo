"""
scraper_by_genre.py - Scrape anime berdasarkan genre dari Otakudesu.

Jalankan:
    python tools/scraper_by_genre.py --list
    python tools/scraper_by_genre.py --genre action
    python tools/scraper_by_genre.py --genre romance --pages 3
    python tools/scraper_by_genre.py --genre all
    python tools/scraper_by_genre.py --genre action --slugs-only
"""
import sys
import re
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
#  PATH FIX — supaya bisa import dari root project
# ═══════════════════════════════════════════════════════════
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bs4 import BeautifulSoup
from core.fetcher import fetch, AllMirrorsFailedError
from config import settings


# ═══════════════════════════════════════════════════════════
#  CONFIG — Output ke data/base/dump/
# ═══════════════════════════════════════════════════════════
OUTPUT_DIR = _ROOT / "data" / "base" / "dump"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GENRE_CACHE = OUTPUT_DIR / "genre_cache.json"
SLUG_OUTPUT = OUTPUT_DIR / "slug_by_genre.json"
SLUG_LIST_DIR = OUTPUT_DIR / "slugs"
SLUG_LIST_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════
#  COLORS
# ═══════════════════════════════════════════════════════════
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


def cprint(text, color=""):
    print(f"{color}{text}{C.RESET}")


def section(title):
    print()
    cprint("=" * 72, C.CYAN)
    cprint("  " + title, C.BOLD + C.CYAN)
    cprint("=" * 72, C.CYAN)


# ═══════════════════════════════════════════════════════════
#  FETCH GENRE LIST
# ═══════════════════════════════════════════════════════════
def fetch_genre_list():
    """Ambil daftar genre dari Otakudesu."""
    section("📋 FETCH DAFTAR GENRE")

    try:
        soup, html = fetch("/genre-list/", source="otakudesu")
    except AllMirrorsFailedError as e:
        cprint(f"  ❌ Gagal fetch: {e}", C.RED)
        return []

    if not soup:
        cprint("  ❌ Response kosong", C.RED)
        return []

    genres = []
    seen = set()

    for a in soup.select(".genres li a, .genre-list a, a[href*='/genres/']"):
        href = a.get("href", "")
        if "/genres/" not in href:
            continue

        m = re.search(r"/genres/([^/]+)/?", href)
        if not m:
            continue

        slug = m.group(1).strip()
        name = a.get_text(strip=True)

        if not slug or not name or slug in seen:
            continue

        seen.add(slug)
        genres.append({
            "slug": slug,
            "name": name,
            "url": href,
        })

    genres.sort(key=lambda x: x["slug"])

    cprint(f"  ✅ Ditemukan {len(genres)} genre", C.GREEN)

    # Cache
    try:
        GENRE_CACHE.write_text(
            json.dumps({
                "fetched_at": datetime.now().isoformat(),
                "genres": genres,
            }, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        cprint(f"  💾 Cached: {GENRE_CACHE}", C.DIM)
    except Exception as e:
        cprint(f"  ⚠️  Gagal cache: {e}", C.YELLOW)

    return genres


def load_genre_cache():
    """Load genre dari cache."""
    if not GENRE_CACHE.exists():
        return None
    try:
        data = json.loads(GENRE_CACHE.read_text(encoding="utf-8"))
        return data.get("genres", [])
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
#  SCRAPE ANIME BY GENRE
# ═══════════════════════════════════════════════════════════
def scrape_genre_anime(genre_slug, max_pages=10):
    """Scrape anime dari halaman genre."""
    print()
    cprint(f"  🎯 Genre: {genre_slug}", C.BOLD + C.CYAN)

    results = []
    seen_slugs = set()
    page = 1

    while page <= max_pages:
        if page == 1:
            path = f"/genres/{genre_slug}/"
        else:
            path = f"/genres/{genre_slug}/page/{page}/"

        print(f"  📄 Page {page}: {path}")

        try:
            soup, html = fetch(path, source="otakudesu")
        except AllMirrorsFailedError as e:
            cprint(f"     ❌ Fetch gagal: {e}", C.RED)
            break

        if not soup:
            cprint(f"     ⚠️  Response kosong", C.YELLOW)
            break

        items = soup.select(".col-anime, .venz li, .anime-list li")

        if not items:
            items = soup.select("article.anime, .detpost")

        if not items:
            cprint(f"     ⚠️  Tidak ada item di page {page}", C.YELLOW)
            break

        page_count = 0
        for item in items:
            link = item.select_one("a[href*='/anime/']")
            if not link:
                continue

            href = link.get("href", "")
            m = re.search(r"/anime/([^/]+)/?", href)
            if not m:
                continue

            slug = m.group(1).strip()
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            title_el = item.select_one(".col-anime-title, .jdlflx a, h2 a, .title")
            title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)

            studio_el = item.select_one(".col-anime-studio, .studio")
            studio = studio_el.get_text(strip=True) if studio_el else ""

            ep_el = item.select_one(".col-anime-eps, .eps")
            ep_text = ep_el.get_text(strip=True) if ep_el else ""
            ep_count = None
            m_ep = re.search(r"(\d+)", ep_text)
            if m_ep:
                ep_count = int(m_ep.group(1))

            rating_el = item.select_one(".col-anime-rating, .rating")
            rating = None
            if rating_el:
                m_r = re.search(r"([\d.]+)", rating_el.get_text(strip=True))
                if m_r:
                    try:
                        rating = float(m_r.group(1))
                    except ValueError:
                        pass

            status_el = item.select_one(".col-anime-status, .status")
            status = status_el.get_text(strip=True) if status_el else ""

            poster_el = item.select_one("img")
            poster = poster_el.get("src", "") if poster_el else ""

            results.append({
                "slug": slug,
                "title": title,
                "url": href,
                "studio": studio,
                "episodes": ep_count,
                "rating": rating,
                "status": status,
                "poster": poster,
            })
            page_count += 1

        print(f"     ✅ {page_count} anime (total: {len(results)})")

        if page_count == 0:
            break

        next_page = soup.select_one("a.next, .pagination a.next, a[href*='/page/']")
        if not next_page:
            print(f"     ℹ️  Halaman terakhir")
            break

        page += 1
        time.sleep(1.5)

    return results


# ═══════════════════════════════════════════════════════════
#  SAVE OUTPUT (ke data/base/dump/)
# ═══════════════════════════════════════════════════════════
def save_slug_json(genre_slug, animes, output_file=None):
    """Simpan hasil scrape ke JSON (nested format)."""
    output = Path(output_file) if output_file else SLUG_OUTPUT

    existing = {}
    if output.exists():
        try:
            existing = json.loads(output.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    existing[genre_slug] = {
        "scraped_at": datetime.now().isoformat(),
        "count": len(animes),
        "animes": animes,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output


def save_slug_list(genre_slug, animes, output_file=None):
    """Simpan hanya daftar slug (format SLUG_N)."""
    output = Path(output_file) if output_file else SLUG_LIST_DIR / f"slug_{genre_slug}.json"

    slugs = {}
    for i, a in enumerate(sorted(animes, key=lambda x: x["title"].lower()), 1):
        slugs[f"SLUG_{i}"] = a["slug"]

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(slugs, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output


# ═══════════════════════════════════════════════════════════
#  DISPLAY
# ═══════════════════════════════════════════════════════════
def display_animes(animes, limit=20):
    if not animes:
        cprint("  (tidak ada anime)", C.YELLOW)
        return

    print()
    print(f"  {'#':<4} {'SLUG':<35} {'RATING':<8} {'STATUS'}")
    cprint("  " + "-" * 70, C.DIM)

    for i, a in enumerate(animes[:limit], 1):
        slug = a["slug"][:33] if len(a["slug"]) <= 35 else a["slug"][:32] + "…"
        rating = f"{a['rating']:.1f}" if a["rating"] else "-"
        status = a["status"][:12] if a["status"] else "-"
        print(f"  {i:<4} {slug:<35} {rating:<8} {status}")

    if len(animes) > limit:
        print(f"  ... dan {len(animes) - limit} lagi")


def display_genres(genres):
    if not genres:
        cprint("  (tidak ada genre)", C.YELLOW)
        return

    print()
    print(f"  {'#':<4} {'SLUG':<25} {'NAMA'}")
    cprint("  " + "-" * 60, C.DIM)

    for i, g in enumerate(genres, 1):
        print(f"  {i:<4} {g['slug']:<25} {g['name']}")


# ═══════════════════════════════════════════════════════════
#  SCRAPE ALL GENRES
# ═══════════════════════════════════════════════════════════
def scrape_all_genres(max_pages_per_genre=5):
    genres = load_genre_cache() or fetch_genre_list()

    if not genres:
        cprint("  ❌ Tidak ada genre", C.RED)
        return

    section(f"🎯 SCRAPE SEMUA GENRE ({len(genres)})")

    all_results = {}
    total_anime = 0

    for i, g in enumerate(genres, 1):
        print()
        cprint(f"  [{i}/{len(genres)}] Genre: {g['name']} ({g['slug']})",
               C.BOLD + C.CYAN)

        try:
            animes = scrape_genre_anime(g["slug"], max_pages=max_pages_per_genre)
            all_results[g["slug"]] = animes
            total_anime += len(animes)
            cprint(f"     ✅ {len(animes)} anime", C.GREEN)
        except Exception as e:
            cprint(f"     ❌ Gagal: {e}", C.RED)

        save_slug_json(g["slug"], animes)

        if i < len(genres):
            time.sleep(2)

    section("📊 RINGKASAN")
    print(f"  Total genre    : {len(all_results)}")
    print(f"  Total anime    : {total_anime}")
    print()
    print("  Per genre:")
    for slug, animes in sorted(all_results.items()):
        print(f"    {slug:<25} {len(animes):>5} anime")

    print()
    cprint(f"  💾 Saved: {SLUG_OUTPUT}", C.GREEN)


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(
        description="Scrape anime by genre dari Otakudesu",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python tools/scraper_by_genre.py --list
  python tools/scraper_by_genre.py --genre action
  python tools/scraper_by_genre.py --genre romance --pages 3
  python tools/scraper_by_genre.py --genre all --pages 5
  python tools/scraper_by_genre.py --genre action --slugs-only
""",
    )
    ap.add_argument("--list", "-l", action="store_true",
                    help="List semua genre")
    ap.add_argument("--genre", "-g", type=str,
                    help="Genre slug (mis. 'action') atau 'all'")
    ap.add_argument("--pages", "-p", type=int, default=5,
                    help="Max halaman per genre (default: 5)")
    ap.add_argument("--slugs-only", action="store_true",
                    help="Output hanya daftar slug (SLUG_N format)")
    ap.add_argument("--output", "-o", type=str,
                    help="Custom output file")
    ap.add_argument("--refresh-genres", action="store_true",
                    help="Force refresh genre cache")
    ap.add_argument("--show", action="store_true",
                    help="Tampilkan hasil scrape")

    args = ap.parse_args()

    # Header
    print()
    cprint("=" * 72, C.CYAN)
    cprint("  SCRAPER BY GENRE", C.BOLD + C.CYAN)
    cprint("=" * 72, C.CYAN)
    print(f"  📁 Output: {OUTPUT_DIR}")
    print()

    # ─── LIST GENRE ───
    if args.list or (not args.genre and not args.refresh_genres):
        genres = None
        if not args.refresh_genres:
            genres = load_genre_cache()

        if not genres:
            genres = fetch_genre_list()

        if genres:
            section(f"📋 DAFTAR GENRE ({len(genres)})")
            display_genres(genres)
            print()
            cprint(f"  💡 Pakai: python tools/scraper_by_genre.py --genre <slug>",
                   C.DIM)
        return

    # ─── REFRESH ───
    if args.refresh_genres and not args.genre:
        genres = fetch_genre_list()
        display_genres(genres)
        return

    # ─── SCRAPE ───
    if args.genre:
        if args.genre.lower() == "all":
            scrape_all_genres(max_pages_per_genre=args.pages)
            return

        genres = load_genre_cache() or fetch_genre_list()
        genre_info = next((g for g in genres if g["slug"] == args.genre.lower()), None)

        if not genre_info:
            cprint(f"  ⚠️  Genre '{args.genre}' tidak ada di cache", C.YELLOW)
            cprint(f"  💡 Jalankan: python tools/scraper_by_genre.py --list", C.DIM)
            return

        section(f"🎯 SCRAPE GENRE: {genre_info['name']}")

        animes = scrape_genre_anime(args.genre, max_pages=args.pages)

        if not animes:
            cprint("  ⚠️  Tidak ada anime", C.YELLOW)
            return

        if args.slugs_only:
            out = save_slug_list(args.genre, animes, args.output)
        else:
            out = save_slug_json(args.genre, animes, args.output)

        section("📊 HASIL")
        print(f"  Genre    : {genre_info['name']} ({args.genre})")
        print(f"  Anime    : {len(animes)}")
        print(f"  File     : {out}")

        if args.show or True:
            display_animes(animes, limit=30)

        cprint(f"\n  💾 Saved: {out}", C.GREEN)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted\n")