"""
debug_html.py — Debug parser + data flow (single mirror).

Jalankan:
    python debug_html.py
    python debug_html.py --url /anime/xxx
    python debug_html.py --url /anime/xxx --slug xxx
    python debug_html.py --url /anime/xxx --source otakudesu
"""
import sys
import json
import time
import socket
from pathlib import Path
from urllib.parse import urlparse

# Path fix
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from bs4 import BeautifulSoup
from pathlib import Path
import sys
# ═══════════════════════════════════════════════════════════
#  PATH FIX — supaya bisa import dari root project
# ═══════════════════════════════════════════════════════════
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# ═══════════════════════════════════════════════════════════

from config import settings
from core.fetcher import (
    fetch, is_blocked, check_source,
    AllMirrorsFailedError, UnknownSourceError,
    MIN_VALID_HTML_SIZE, BLOCK_KEYWORDS,
)
from core.sources.otakudesu import OtakudesuParser


# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
SEP = "═" * 72
SUB = "─" * 72

DEBUG_DIR = Path("data" / "debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def section(title, icon="🔷"):
    print(f"\n{SEP}\n{icon} {title}\n{SEP}")


def subsection(title):
    print(f"\n{SUB}\n── {title}\n{SUB}")


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def debug_html(path_or_url, source="otakudesu", slug=None):
    # Banner
    print(f"\n{SEP}")
    print(f"🐛 DEBUG HTML & PARSER (SINGLE MIRROR)")
    print(f"{SEP}")
    print(f"🎯 Target : {path_or_url}")
    print(f"📡 Source : {source}")
    print(f"{SEP}")

    # ═══════════════════════════════════════════════════════
    #  STEP 0 — CEK SOURCE CONFIG
    # ═══════════════════════════════════════════════════════
    section("STEP 0 — CEK SOURCE CONFIG", "⚙️")

    src = settings.get_source(source)
    if not src:
        print(f"❌ Source '{source}' tidak ada di config")
        print(f"   Tersedia: {list(settings.sources.keys())}")
        return

    print(f"📌 Name       : {src.name}")
    print(f"📌 Enabled    : {src.enabled}")
    print(f"📌 Base URL   : {src.base_url}")
    print(f"📌 Shortener  : {src.shortener_hosts}")

    if not src.enabled:
        print(f"\n⚠️  Source '{source}' DISABLED — set {source.upper()}_ENABLED=true di .env")
        return

    if not src.base_url:
        print(f"\n⚠️  Base URL kosong — set {source.upper()}_BASE_URL di .env")
        return

    # ═══════════════════════════════════════════════════════
    #  STEP 1 — CEK DNS & KONEKSI
    # ═══════════════════════════════════════════════════════
    section("STEP 1 — DNS & KONEKSI", "🌐")

    domain = urlparse(src.base_url).netloc
    print(f"🌐 Domain: {domain}")

    try:
        ip = socket.gethostbyname(domain)
        print(f"✅ DNS   : {ip}")

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        result = s.connect_ex((domain, 443))
        s.close()

        if result == 0:
            print(f"✅ Port 443: open")
        else:
            print(f"❌ Port 443: closed (kode {result})")
            return
    except Exception as e:
        print(f"❌ DNS/koneksi gagal: {e}")
        return

    # ═══════════════════════════════════════════════════════
    #  STEP 2 — FETCH HTML
    # ═══════════════════════════════════════════════════════
    section("STEP 2 — FETCH HTML", "📥")

    # Build URL lengkap
    if path_or_url.startswith("http"):
        full_url = path_or_url
    else:
        full_url = src.base_url + (
            path_or_url if path_or_url.startswith("/") else "/" + path_or_url
        )

    print(f"🔗 URL: {full_url}")
    print(f"⏱️  Timeout: {settings.request_timeout}s")
    print(f"🔄 Retry: {settings.max_retry}x\n")

    t0 = time.time()
    try:
        soup, html = fetch(path_or_url, source=source)
        elapsed = time.time() - t0
    except AllMirrorsFailedError as e:
        elapsed = time.time() - t0
        print(f"\n❌ FETCH GAGAL ({elapsed:.2f}s)")
        print(f"   {e}")

        # Diagnosa tambahan
        subsection("Diagnosa")
        print("   Kemungkinan penyebab:")
        print("   1. Server Otakudesu sedang overload ('server is busy')")
        print("   2. IP Anda diblok sementara")
        print("   3. Koneksi internet bermasalah")
        print("   4. Cloudflare challenge")
        print("\n   Solusi:")
        print("   - Coba lagi beberapa menit kemudian")
        print("   - Test manual di browser: buka " + full_url)
        print("   - Ganti mirror/domain di .env")
        return

    except UnknownSourceError as e:
        print(f"\n❌ SOURCE ERROR: {e}")
        return

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"\n✅ FETCH SUKSES ({elapsed:.2f}s)")
    print(f"   HTML size: {len(html):,} chars")

    # ═══════════════════════════════════════════════════════
    #  STEP 3 — ANALISA HTML
    # ═══════════════════════════════════════════════════════
    section("STEP 3 — ANALISA HTML", "🔍")

    # Simpan HTML
    dump_path = DEBUG_DIR / f"debug_{slug or 'page'}.html"
    dump_path.write_text(html, encoding="utf-8")
    print(f"💾 Disimpan: {dump_path.resolve()}")

    # Cek block
    subsection("Cek Block/Error")
    is_block = is_blocked(html)

    if is_block:
        print(f"   🚨 HTML TERINDIKASI BLOCK/ERROR")
        lower = html.lower()
        for kw in BLOCK_KEYWORDS:
            if kw in lower:
                print(f"      • Keyword ditemukan: '{kw}'")
    else:
        print(f"   ✅ HTML terlihat normal")

    if len(html) < MIN_VALID_HTML_SIZE:
        print(f"   ⚠️  HTML terlalu pendek (< {MIN_VALID_HTML_SIZE} chars)")

    # Title
    soup_check = BeautifulSoup(html, "lxml")
    title_tag = soup_check.find("title")
    print(f"\n   📄 <title>: {title_tag.get_text(strip=True)[:80] if title_tag else '(kosong)'}")

    # Preview isi HTML kalau pendek
    if len(html) < 5000:
        subsection("Preview HTML (file kecil)")
        preview = html[:1500].replace("\n", " ").replace("\r", "")
        print(f"   {preview}")
        print(f"   ... (total {len(html)} chars)")

    # Signature parser
    subsection("Signature Parser Otakudesu")
    signatures = {
        "infozingle": ".infozingle",
        "infozin": ".infozin",
        "sinopc": ".sinopc",
        "fotoanime": ".fotoanime",
        "episodelist": ".episodelist",
        "jdlrx": ".jdlrx",
    }

    found_sig = 0
    for name, sel in signatures.items():
        n = len(soup_check.select(sel))
        icon = "✅" if n else "❌"
        if n:
            found_sig += 1
        print(f"   {icon} {sel:<20} → {n}")

    if found_sig == 0:
        print(f"\n   🚨 TIDAK ADA SIGNATURE PARSER DITEMUKAN!")
        print(f"      HTML mungkin bukan halaman anime Otakudesu")
        print(f"      atau struktur website berubah")

    # ═══════════════════════════════════════════════════════
    #  STEP 4 — PARSER METADATA
    # ═══════════════════════════════════════════════════════
    section("STEP 4 — PARSER METADATA", "📋")

    parser = OtakudesuParser(base_url=src.base_url)

    try:
        meta = parser.extract_metadata(soup)
    except Exception as e:
        print(f"❌ extract_metadata error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return

    # Pretty print
    print(f"📌 Judul       : {meta.get('title')!r}")
    print(f"📌 Judul JP    : {(meta.get('title_jp') or '')[:60]!r}")
    print(f"📌 Studio      : {meta.get('studio')!r}")
    print(f"📌 Produser    : {meta.get('producer')!r}")
    print(f"📌 Tipe        : {meta.get('type')!r}")
    print(f"📌 Status      : {meta.get('status')!r}")
    print(f"📌 Total Ep    : {meta.get('total_episode')!r}")
    print(f"📌 Durasi      : {meta.get('duration')!r}")
    print(f"📌 Rilis       : {meta.get('release_date')!r}")
    print(f"📌 Rating      : {meta.get('rating')!r}")
    print(f"📌 Poster      : {(meta.get('poster') or '')[:60]!r}")
    print(f"📌 Genre       : {meta.get('genres')!r}")
    print(f"📌 Sinopsis    : {(meta.get('synopsis') or '')[:80]!r}")
    print(f"📌 Info keys   : {list(meta.get('info', {}).keys())}")

    # Cek field kosong
    subsection("Field Kosong (potensi bug)")
    empty_fields = []
    for k, v in meta.items():
        if k == "rating":
            continue
        if not v:
            empty_fields.append(k)

    if empty_fields:
        for f in empty_fields:
            print(f"   ⚠️  {f}")
    else:
        print("   ✅ Semua field terisi")

    # ═══════════════════════════════════════════════════════
    #  STEP 5 — PARSER EPISODE
    # ═══════════════════════════════════════════════════════
    section("STEP 5 — PARSER EPISODE LIST", "📺")

    try:
        episodes = parser.extract_episodes(soup)
    except Exception as e:
        print(f"❌ extract_episodes error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"📊 Total episode: {len(episodes)}")
    for i, ep in enumerate(episodes[:10], 1):
        print(f"\n   [{i}] #{ep.get('episode_number')}")
        print(f"       Title: {ep.get('title', '')[:60]}")
        print(f"       URL  : {ep.get('url', '')[:70]}")
        print(f"       Slug : {ep.get('slug')}")

    if not episodes:
        subsection("Cari Link Episode Manual")
        all_links = soup.find_all("a", href=True)
        ep_links = [
            a for a in all_links
            if "/episode/" in a["href"] or "episode" in a["href"].lower()
        ]
        print(f"   📊 Total <a>: {len(all_links)}")
        print(f"   📊 <a> dengan 'episode': {len(ep_links)}")
        print(f"\n   Sample 5 link:")
        for a in all_links[:5]:
            print(f"      - {a.get_text(strip=True)[:40]!r}")
            print(f"        href: {a.get('href', '')[:70]}")

    # ═══════════════════════════════════════════════════════
    #  STEP 6 — PARSER EPISODE DETAIL
    # ═══════════════════════════════════════════════════════
    if episodes:
        section("STEP 6 — PARSER EPISODE DETAIL", "🎬")

        ep_url = episodes[0]["url"]
        print(f"🎯 Episode 1: {ep_url}")
        print(f"⏱️  Delay 1.5s sebelum fetch...\n")

        time.sleep(1.5)

        try:
            from core.extractors import parse_episode
            ep_data = parse_episode(ep_url, source=source)

            print(f"📌 Judul        : {ep_data.get('title')!r}")
            print(f"📌 Slug         : {ep_data.get('slug')!r}")
            print(f"📌 Stream count : {len(ep_data.get('streams', []))}")
            for s in ep_data.get("streams", [])[:3]:
                print(f"      • [{s.get('host')}] {s.get('url', '')[:60]}")

            print(f"\n📌 Download cnt : {len(ep_data.get('downloads', []))}")
            for d in ep_data.get("downloads", [])[:5]:
                print(f"      • [{d.get('quality'):<12}] {d.get('host'):<12}")

        except Exception as e:
            print(f"❌ parse_episode error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    # ═══════════════════════════════════════════════════════
    #  STEP 7 — SIMULASI DATA UNTUK DB
    # ═══════════════════════════════════════════════════════
    section("STEP 7 — SIMULASI DATA UNTUK DB", "💾")

    result = {
        "source": source,
        "url": full_url,
        "slug": slug or path_or_url.rstrip("/").split("/")[-1],
        "metadata": meta,
        "episodes": episodes,
        "episode_details": [],
    }

    # Test _extract_slug
    subsection("Test _extract_slug")
    try:
        from db.repository import _extract_slug
        extracted_slug = _extract_slug(result)
        print(f"   ✅ Slug: {extracted_slug!r}")
    except Exception as e:
        print(f"   ❌ _extract_slug error: {e}")
        extracted_slug = None

    # Simulasi anime_data
    subsection("anime_data (akan dikirim ke DB)")
    meta_for_db = result["metadata"]
    anime_data = {
        "source": source,
        "slug": extracted_slug,
        "url": result["url"],
        "title": meta_for_db.get("title") or "",
        "title_jp": meta_for_db.get("title_jp") or "",
        "synopsis": meta_for_db.get("synopsis") or "",
        "poster_url": meta_for_db.get("poster") or "",
        "studio": meta_for_db.get("studio") or "",
        "producer": meta_for_db.get("producer") or "",
        "type": meta_for_db.get("type") or "",
        "status": meta_for_db.get("status") or "",
        "duration": meta_for_db.get("duration") or "",
        "release_date": meta_for_db.get("release_date") or "",
        "total_episode": meta_for_db.get("total_episode"),
        "rating": meta_for_db.get("rating"),
        "genres": meta_for_db.get("genres") or [],
        "info": meta_for_db.get("info") or {},
    }
    print(json.dumps(anime_data, indent=2, ensure_ascii=False, default=str))

    # Cek field kosong
    subsection("Field Kosong di anime_data")
    empty_db = []
    for k, v in anime_data.items():
        if k in ("rating", "total_episode"):
            continue
        if not v:
            empty_db.append(k)

    if empty_db:
        print(f"   ⚠️  Fields kosong: {empty_db}")
        print(f"   ⚠️  Data akan tersimpan dengan field kosong di DB")
    else:
        print("   ✅ Semua field terisi")

    # ═══════════════════════════════════════════════════════
    #  STEP 8 — CEK DB SAAT INI
    # ═══════════════════════════════════════════════════════
    section("STEP 8 — CEK DB SAAT INI", "🗄️")

    try:
        from db import get_session
        from db.repository import AnimeRepository

        with get_session() as s:
            anime = AnimeRepository.get_by_slug(s, extracted_slug) if extracted_slug else None

            if anime:
                print(f"📌 DB record DITEMUKAN:")
                print(f"   ID        : {anime.id}")
                print(f"   Slug      : {anime.slug}")
                print(f"   Title     : {anime.title!r}")
                print(f"   Studio    : {anime.studio!r}")
                print(f"   Genres    : {anime.genres!r}")
                print(f"   Episodes  : {len(anime.episodes)}")
                print(f"   Scraped   : {anime.scraped_at}")
                print(f"   Updated   : {anime.updated_at}")

                if not anime.title:
                    print(f"\n   🚨 DB record ada tapi TITLE KOSONG!")
                    print(f"      → Perlu delete + re-scrape")
            else:
                print(f"📌 DB record: TIDAK ADA")
                print(f"   → Perlu scrape pertama kali")

    except Exception as e:
        print(f"❌ DB check error: {e}")
        import traceback
        traceback.print_exc()

    # ═══════════════════════════════════════════════════════
    #  STEP 9 — HEALTH CHECK SOURCE
    # ═══════════════════════════════════════════════════════
    section("STEP 9 — HEALTH CHECK SOURCE", "🏥")

    try:
        result_hc = check_source(source)
        for mirror, m in result_hc.get("mirrors", {}).items():
            icon = "✅" if m["alive"] else "❌"
            lat = f"{m['latency_ms']}ms" if m["latency_ms"] else "-"
            err = f" ({m.get('error', '')})" if m.get("error") else ""
            print(f"   {icon} [{m['status']:>3}] {lat:>7}  {mirror}{err}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

    # ═══════════════════════════════════════════════════════
    #  RINGKASAN
    # ═══════════════════════════════════════════════════════
    section("📊 RINGKASAN", "🏁")

    issues = []
    fixes = []

    # Cek HTML
    if is_block:
        issues.append("🚨 HTML terindikasi block/error")
        fixes.append("Tunggu beberapa menit, coba lagi")

    if len(html) < MIN_VALID_HTML_SIZE:
        issues.append(f"⚠️  HTML pendek ({len(html)} chars)")
        fixes.append("Cek apakah Otakudesu sedang down")

    # Cek parser
    if not meta.get("title"):
        issues.append("❌ metadata.title KOSONG")
        fixes.append("Selector parser mungkin berubah")

    if not meta.get("genres"):
        issues.append("⚠️  metadata.genres KOSONG")

    if not episodes:
        issues.append("❌ episodes KOSONG")

    # Cek slug
    if not extracted_slug:
        issues.append("❌ slug tidak bisa di-extract")

    # Cek DB
    if "anime" in locals() and anime and not anime.title:
        issues.append("❌ DB record ada tapi kosong")

    # Print
    if issues:
        print("\n⚠️  MASALAH TERDETEKSI:")
        for i in issues:
            print(f"   {i}")

        print("\n💡 SOLUSI:")
        for f in fixes:
            print(f"   → {f}")
    else:
        print("\n✅ Semua OK — data flow sehat")

    print(f"\n💾 HTML tersimpan: {dump_path.resolve()}")
    print(f"   Buka di browser untuk inspeksi manual.")
    print()


# ═══════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Debug parser HTML (single mirror)")
    ap.add_argument("--url", "-u", default="/anime/yowaki-max-sub-indo",
                    help="Path atau URL anime")
    ap.add_argument("--source", "-s", default="otakudesu",
                    help="Source (otakudesu|kuramanime|animeindo)")
    ap.add_argument("--slug", default=None,
                    help="Slug untuk nama file debug")
    args = ap.parse_args()

    debug_html(args.url, source=args.source, slug=args.slug)