"""
scraper_update.py - Scrape anime terbaru dari Otakudesu.

Jalankan:
    python tools/scraper_update.py                 # default (10 anime terbaru)
    python tools/scraper_update.py --limit 20      # 20 anime
    python tools/scraper_update.py --all           # semua ongoing
    python tools/scraper_update.py --dry-run       # cek dulu
    python tools/scraper_update.py --json          # simpan JSON saja
    python tools/scraper_update.py --db-only       # simpan DB saja
    python tools/scraper_update.py --no-db         # skip DB
"""
import sys
import re
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
#  PATH FIX
# ═══════════════════════════════════════════════════════════
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ROOT = _ROOT


# ═══════════════════════════════════════════════════════════
#  IMPORTS
# ═══════════════════════════════════════════════════════════
from core.fetcher import fetch, AllMirrorsFailedError


# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
BASE_DIR = ROOT / "data" / "base"
DUMP_DIR = BASE_DIR / "dump"
DUMP_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = DUMP_DIR / "anime_latest.json"


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
#  FETCH ONGOING ANIME
# ═══════════════════════════════════════════════════════════
def fetch_ongoing_anime():
    """
    Ambil daftar anime on-going dari Otakudesu.
    URL: https://otakudesu.blog/ongoing-anime/
    """
    section("🌐 FETCH ANIME TERBARU")
    print()
    print("  📄 Halaman: /ongoing-anime/")
    print("  🌐 Fetch dari Otakudesu...")

    try:
        soup, html = fetch("/ongoing-anime/", source="otakudesu")
    except AllMirrorsFailedError as e:
        cprint(f"\n  ❌ Gagal fetch: {e}", C.RED)
        return []

    if not soup:
        cprint("  ❌ Response kosong", C.RED)
        return []

    animes = []
    seen = set()

    # Struktur Otakudesu: .venz > ul > li
    for li in soup.select(".venz > ul > li, .venz ul li"):
        link = li.select_one(".jdlflx a, a[href*='/anime/']")
        if not link:
            continue

        href = link.get("href", "")
        m = re.search(r"/anime/([^/]+)/?", href)
        if not m:
            continue

        slug = m.group(1).strip()
        if not slug or slug in seen:
            continue
        seen.add(slug)

        # Title
        title = link.get_text(strip=True)

        # Poster
        img = li.select_one(".thumb img, img")
        poster = img.get("src", "") if img else ""

        # Episode terbaru
        ep_el = li.select_one(".epz")
        ep_text = ep_el.get_text(strip=True) if ep_el else ""

        # Episode number
        ep_num = None
        m_ep = re.search(r"(\d+)", ep_text)
        if m_ep:
            ep_num = int(m_ep.group(1))

        # Hari rilis
        day_el = li.select_one(".zeebr")
        day = day_el.get_text(strip=True) if day_el else ""

        animes.append({
            "slug": slug,
            "title": title,
            "url": href,
            "poster": poster,
            "episode_text": ep_text,
            "episode_number": ep_num,
            "day": day,
            "scraped_at": datetime.now().isoformat(),
        })

    cprint(f"\n  ✅ Ditemukan {len(animes)} anime ongoing", C.GREEN)
    return animes


# ═══════════════════════════════════════════════════════════
#  DISPLAY ANIME
# ═══════════════════════════════════════════════════════════
def display_animes(animes, limit=20):
    """Tampilkan list anime."""
    if not animes:
        cprint("  (tidak ada anime)", C.YELLOW)
        return

    print()
    print(f"  {'#':<4} {'SLUG':<35} {'EP':<6} {'HARI':<12}")
    cprint("  " + "-" * 70, C.DIM)

    for i, a in enumerate(animes[:limit], 1):
        slug = a["slug"][:33] if len(a["slug"]) <= 35 else a["slug"][:32] + "…"
        ep = str(a["episode_number"]) if a["episode_number"] else "-"
        day = a["day"][:10] if a["day"] else "-"
        print(f"  {i:<4} {slug:<35} {ep:<6} {day}")

    if len(animes) > limit:
        print(f"  ... dan {len(animes) - limit} lagi")


# ═══════════════════════════════════════════════════════════
#  SAVE JSON
# ═══════════════════════════════════════════════════════════
def save_json(animes, output_file=None):
    """Simpan hasil ke JSON."""
    output = Path(output_file) if output_file else OUTPUT_FILE

    data = {
        "scraped_at": datetime.now().isoformat(),
        "source": "otakudesu",
        "count": len(animes),
        "animes": animes,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    cprint(f"  ✅ JSON tersimpan: {output}", C.GREEN)
    print(f"  📊 Total: {len(animes)} anime")
    print(f"  💾 Size : {output.stat().st_size:,} bytes")

    return output


# ═══════════════════════════════════════════════════════════
#  SAVE TO DB
# ═══════════════════════════════════════════════════════════
def save_to_db(slugs, follow_all=False):
    """
    Simpan ke DB. Scrape detail dulu, lalu save.

    Return: dict counters
    """
    section("💾 SIMPAN KE DB")
    print()

    try:
        from core.pipeline import scrape_anime
        from db.repository import save_scrape_result, AnimeRepository
        from db import get_session
    except ImportError as e:
        cprint(f"  ❌ Import error: {e}", C.RED)
        return {"ok": 0, "skip": 0, "fail": 0}

    counters = {"ok": 0, "skip": 0, "fail": 0, "details": []}

    for i, slug in enumerate(slugs, 1):
        print(f"  [{i}/{len(slugs)}] {slug}")

        # Cek existing
        try:
            with get_session() as s:
                existing = AnimeRepository.get_by_slug(s, slug)
                if existing and existing.title:
                    print(f"     ⏭️  SKIP (sudah ada)")
                    counters["skip"] += 1
                    continue
        except Exception:
            pass

        # Scrape
        try:
            t0 = time.time()
            result = scrape_anime(
                path_or_url=f"/anime/{slug}",
                source="otakudesu",
                follow_all=follow_all,
                resolve=False,
                filter_dead=False,
            )
            counters_db = save_scrape_result(result)
            dt = time.time() - t0

            print(f"     ✅ OK ({dt:.1f}s) — "
                  f"{counters_db['episodes']} ep, {counters_db['downloads']} dl")
            counters["ok"] += 1
            counters["details"].append({
                "slug": slug,
                "status": "ok",
                "counters": counters_db,
            })
        except Exception as e:
            print(f"     ❌ FAIL: {type(e).__name__}: {str(e)[:100]}")
            counters["fail"] += 1
            counters["details"].append({
                "slug": slug,
                "status": "fail",
                "error": str(e)[:150],
            })

        # Rate limit
        if i < len(slugs):
            time.sleep(1.5)

    return counters


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(
        description="Scrape anime terbaru dari Otakudesu",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python tools/scraper_update.py                  # 10 anime terbaru
  python tools/scraper_update.py --limit 20       # 20 anime
  python tools/scraper_update.py --all            # semua ongoing
  python tools/scraper_update.py --dry-run        # preview saja
  python tools/scraper_update.py --json-only      # hanya simpan JSON
  python tools/scraper_update.py --no-save        # tidak simpan
  python tools/scraper_update.py --no-db          # skip DB
  python tools/scraper_update.py --all-episodes   # scrape semua episode
""",
    )
    ap.add_argument("--limit", "-l", type=int, default=10,
                    help="Max anime (default: 10, 0 = semua)")
    ap.add_argument("--all", "-a", action="store_true",
                    help="Ambil semua on-going")
    ap.add_argument("--dry-run", "-n", action="store_true",
                    help="Preview saja, tidak scrape")
    ap.add_argument("--no-db", action="store_true",
                    help="Skip simpan ke DB")
    ap.add_argument("--no-save", action="store_true",
                    help="Skip simpan JSON")
    ap.add_argument("--json-only", action="store_true",
                    help="Hanya simpan JSON, skip DB")
    ap.add_argument("--all-episodes", action="store_true",
                    help="Scrape semua episode (lambat)")
    ap.add_argument("--delay", type=float, default=1.5,
                    help="Jeda antar anime (default: 1.5s)")

    args = ap.parse_args()

    # Header
    print()
    cprint("=" * 72, C.CYAN)
    cprint("  🕷️  SCRAPER UPDATE — Anime Terbaru", C.BOLD + C.CYAN)
    cprint("=" * 72, C.CYAN)
    print()
    print(f"  📁 Root      : {ROOT}")
    print(f"  📁 Output    : {OUTPUT_FILE}")
    print(f"  📊 Limit     : {'Semua' if args.all else args.limit}")
    print(f"  💾 DB        : {'OFF' if args.no_db or args.json_only else 'ON'}")
    print(f"  🎯 Mode      : {'DRY-RUN' if args.dry_run else 'LIVE'}")

    # Fetch
    t0 = time.time()
    animes = fetch_ongoing_anime()

    if not animes:
        cprint("\n  ❌ Tidak ada anime", C.RED)
        return

    # Limit
    if not args.all and args.limit > 0:
        animes = animes[:args.limit]

    total = len(animes)

    # Display
    section(f"📺 DAFTAR ANIME ({total})")
    display_animes(animes, limit=30)

    # Dry-run
    if args.dry_run:
        print()
        cprint("  💡 Dry-run — tidak scrape", C.YELLOW)
        return

    # Konfirmasi
    print()
    cprint(f"  🎯 Akan scrape {total} anime", C.BOLD)
    print(f"     Follow all episodes: {args.all_episodes}")
    print()

    try:
        confirm = input("  Lanjutkan? (Y/n): ").strip().lower()
        if confirm and confirm not in ("y", "ya", "yes"):
            cprint("  ❌ Dibatalkan", C.YELLOW)
            return
    except KeyboardInterrupt:
        print()
        return

    # Save JSON dulu
    if not args.no_save:
        save_json(animes)

    # Save DB
    if not args.no_db and not args.json_only:
        slugs = [a["slug"] for a in animes]
        db_counters = save_to_db(slugs, follow_all=args.all_episodes)

        # Summary DB
        section("📊 RINGKASAN DB")
        print(f"  ✅ OK   : {db_counters['ok']}")
        print(f"  ⏭️  SKIP : {db_counters['skip']}")
        print(f"  ❌ FAIL : {db_counters['fail']}")

    # Total waktu
    dt = time.time() - t0

    section("✅ SELESAI")
    print(f"  ⏱️  Total waktu : {dt:.1f}s")
    print(f"  📊 Total anime : {total}")
    if not args.no_save:
        print(f"  💾 JSON        : {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⏸️  Interrupted\n")