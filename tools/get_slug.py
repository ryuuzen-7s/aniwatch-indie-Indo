"""
get_slug.py - Extract slug dari slug_by_genre.json.

Jalankan:
    python tools/get_slug.py                      # menu interaktif
    python tools/get_slug.py --all                # ambil semua slug
    python tools/get_slug.py --genre action       # slug genre tertentu
    python tools/get_slug.py --flat               # output flat (SLUG_N)
    python tools/get_slug.py --dedupe             # hapus duplikat
    python tools/get_slug.py --stats              # statistik saja
"""
import sys
import re
import json
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict


# ═══════════════════════════════════════════════════════════
#  PATH FIX
# ═══════════════════════════════════════════════════════════
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ROOT = _ROOT


# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
BASE_DIR = ROOT / "data" / "base"
DUMP_DIR = BASE_DIR / "dump"
SLUGS_DIR = BASE_DIR / "slugs"

SLUGS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_INPUT = DUMP_DIR / "slug_by_genre.json"
DEFAULT_OUTPUT = SLUGS_DIR / "slugs_all.json"
DEFAULT_OUTPUT_BY_GENRE = SLUGS_DIR / "by_genre"


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
#  LOAD JSON
# ═══════════════════════════════════════════════════════════
def load_slug_by_genre(path):
    """
    Load slug_by_genre.json (format nested).

    Format:
        {
          "action": {
            "count": 45,
            "animes": [
              {"slug": "psyren-sub-indo", "title": "Psyren", ...},
              ...
            ]
          },
          ...
        }

    Return: {"action": [anime1, anime2, ...], ...}
    """
    path = Path(path)

    if not path.exists():
        cprint(f"  ❌ File tidak ada: {path}", C.RED)
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        cprint(f"  ❌ Gagal baca JSON: {e}", C.RED)
        return None

    if not isinstance(data, dict):
        cprint("  ❌ Format tidak valid (bukan dict)", C.RED)
        return None

    # Cek apakah nested
    result = {}
    for genre_key, genre_data in data.items():
        if isinstance(genre_data, dict) and "animes" in genre_data:
            animes = genre_data.get("animes", [])
            result[genre_key] = animes
        elif isinstance(genre_data, list):
            result[genre_key] = genre_data
        else:
            # Bukan format yang kita harapkan
            continue

    return result


# ═══════════════════════════════════════════════════════════
#  EXTRACT SLUGS
# ═══════════════════════════════════════════════════════════
def extract_slugs(data, dedupe=True):
    """
    Extract slug dari data.

    Return:
        {
            "by_genre": {"action": [slug1, slug2], ...},
            "all": [slug1, slug2, ...],       # dengan dedupe
            "duplicates": {slug: [genre1, genre2], ...}
        }
    """
    by_genre = {}
    all_slugs = []
    seen = set()
    duplicates = defaultdict(list)

    for genre, animes in data.items():
        slugs = []
        for anime in animes:
            if isinstance(anime, dict):
                slug = anime.get("slug", "").strip()
            elif isinstance(anime, str):
                slug = anime.strip()
            else:
                continue

            if not slug:
                continue

            # Cek duplikat
            if slug in seen:
                duplicates[slug].append(genre)
                if dedupe:
                    continue

            seen.add(slug)
            all_slugs.append(slug)
            slugs.append(slug)

        by_genre[genre] = slugs

    return {
        "by_genre": by_genre,
        "all": all_slugs,
        "duplicates": dict(duplicates),
    }


# ═══════════════════════════════════════════════════════════
#  SAVE FUNCTIONS
# ═══════════════════════════════════════════════════════════
def save_flat(slugs, output_file=None, prefix="SLUG"):
    """Simpan sebagai flat (SLUG_N)."""
    output = Path(output_file) if output_file else DEFAULT_OUTPUT

    result = {f"{prefix}_{i}": slug for i, slug in enumerate(slugs, 1)}

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output, len(result)


def save_by_genre(by_genre, output_dir=None, prefix="SLUG"):
    """Simpan per genre (setiap genre file sendiri)."""
    output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_BY_GENRE
    output_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for genre, slugs in sorted(by_genre.items()):
        if not slugs:
            continue

        result = {f"{prefix}_{i}": slug for i, slug in enumerate(slugs, 1)}

        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", genre)
        out_file = output_dir / f"slug_{safe_name}.json"

        out_file.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        saved.append((genre, out_file, len(slugs)))

    return saved


def save_combined(slugs, genres_info, output_file=None):
    """Simpan combined (flat + metadata)."""
    output = Path(output_file) if output_file else SLUGS_DIR / "slugs_with_meta.json"

    result = {
        "extracted_at": datetime.now().isoformat(),
        "total": len(slugs),
        "slugs": {f"SLUG_{i}": slug for i, slug in enumerate(slugs, 1)},
        "by_genre": genres_info,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output


# ═══════════════════════════════════════════════════════════
#  DISPLAY
# ═══════════════════════════════════════════════════════════
def display_stats(data, extract_result):
    """Tampilkan statistik."""
    section("📊 STATISTIK")

    by_genre = extract_result["by_genre"]
    all_slugs = extract_result["all"]
    duplicates = extract_result["duplicates"]

    print(f"  📁 Total genre     : {len(data)}")
    print(f"  📊 Total slug      : {len(all_slugs)}")
    print(f"  🔁 Duplikat        : {len(duplicates)}")

    print()
    print("  Per genre:")
    print(f"  {'GENRE':<25} {'SLUG':>6}")
    cprint("  " + "-" * 35, C.DIM)

    for genre, slugs in sorted(by_genre.items()):
        bar = "█" * min(len(slugs), 30)
        print(f"  {genre:<25} {len(slugs):>6} {C.GREEN}{bar}{C.RESET}")

    if duplicates:
        print()
        cprint(f"  ⚠️  Duplikat ({len(duplicates)}):", C.YELLOW)
        for slug, genres in list(duplicates.items())[:10]:
            print(f"    {slug}")
            print(f"      └─ muncul di: {', '.join(genres)}")

    # Preview
    print()
    print(f"  Preview 10 slug:")
    for i, slug in enumerate(all_slugs[:10], 1):
        print(f"    {i:>3}. {slug}")


# ═══════════════════════════════════════════════════════════
#  MENU INTERAKTIF
# ═══════════════════════════════════════════════════════════
MENU = """
╔══════════════════════════════════════════════════════════╗
║           🕷️  GET SLUG - Extract Slugs                   ║
╠══════════════════════════════════════════════════════════╣
║  [1] Extract semua → slugs_all.json                      ║
║  [2] Extract per genre → by_genre/                       ║
║  [3] Extract semua + per genre                           ║
║  [4] 📊 Statistik saja                                   ║
║  [5] 📄 Preview isi file                                 ║
║                                                          ║
║  [0] Keluar                                              ║
╚══════════════════════════════════════════════════════════╝
"""


def interactive_menu():
    while True:
        # Header
        section("🕷️  GET SLUG — Extract Slugs")
        print()
        print(f"  📁 Input   : {DEFAULT_INPUT}")
        print(f"  📁 Output  : {SLUGS_DIR}")
        print(MENU)

        choice = input(f"  {C.CYAN}Pilih: {C.RESET}").strip()

        try:
            if choice == "0":
                cprint("\n  👋 Bye!", C.CYAN)
                break

            elif choice in ("1", "2", "3", "4"):
                # Load
                data = load_slug_by_genre(DEFAULT_INPUT)
                if data is None:
                    print()
                    input(f"  {C.DIM}[Enter]{C.RESET}")
                    import os
                    os.system("cls" if os.name == "nt" else "clear")
                    continue

                # Extract
                extract_result = extract_slugs(data, dedupe=True)

                if choice == "4":
                    display_stats(data, extract_result)

                elif choice == "1":
                    display_stats(data, extract_result)
                    print()
                    out, count = save_flat(extract_result["all"])
                    cprint(f"\n  ✅ Saved: {out}", C.GREEN)
                    print(f"     {count} slug")

                elif choice == "2":
                    display_stats(data, extract_result)
                    print()
                    saved = save_by_genre(extract_result["by_genre"])
                    cprint(f"\n  ✅ Saved {len(saved)} file di: {DEFAULT_OUTPUT_BY_GENRE}",
                           C.GREEN)
                    for genre, path, count in saved[:10]:
                        print(f"     {genre:<25} {count:>4} slug → {path.name}")
                    if len(saved) > 10:
                        print(f"     ... dan {len(saved) - 10} lagi")

                elif choice == "3":
                    display_stats(data, extract_result)
                    print()
                    # Save flat
                    out, count = save_flat(extract_result["all"])
                    cprint(f"\n  ✅ Slugs all: {out} ({count} slug)", C.GREEN)

                    # Save per genre
                    saved = save_by_genre(extract_result["by_genre"])
                    cprint(f"  ✅ Per genre: {len(saved)} file di {DEFAULT_OUTPUT_BY_GENRE}",
                           C.GREEN)

                    # Save combined
                    combined = save_combined(
                        extract_result["all"],
                        {g: len(s) for g, s in extract_result["by_genre"].items()},
                    )
                    cprint(f"  ✅ Combined: {combined}", C.GREEN)

            elif choice == "5":
                section("📄 PREVIEW")
                if DEFAULT_INPUT.exists():
                    print()
                    content = DEFAULT_INPUT.read_text(encoding="utf-8")
                    lines = content.split("\n")
                    for line in lines[:40]:
                        print(line)
                    if len(lines) > 40:
                        print(f"... ({len(lines) - 40} lines lagi)")
                else:
                    cprint(f"  ❌ File tidak ada: {DEFAULT_INPUT}", C.RED)

            else:
                cprint("  ❓ Pilihan tidak valid", C.YELLOW)

        except KeyboardInterrupt:
            cprint("\n  ⏸️  Dibatalkan", C.YELLOW)
        except Exception as e:
            cprint(f"  ❌ Error: {type(e).__name__}: {e}", C.RED)

        if choice != "0":
            print()
            input(f"  {C.DIM}[Enter untuk lanjut]{C.RESET}")
            import os
            os.system("cls" if os.name == "nt" else "clear")


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(
        description="Extract slug dari slug_by_genre.json",
    )
    ap.add_argument("--input", "-i", type=str, default=str(DEFAULT_INPUT),
                    help="Path input JSON")
    ap.add_argument("--output", "-o", type=str, default=None,
                    help="Output file (flat)")
    ap.add_argument("--all", "-a", action="store_true",
                    help="Extract semua slug (flat)")
    ap.add_argument("--by-genre", action="store_true",
                    help="Extract per genre")
    ap.add_argument("--combined", action="store_true",
                    help="Extract semua + per genre + combined")
    ap.add_argument("--genre", "-g", type=str, default=None,
                    help="Filter genre tertentu")
    ap.add_argument("--stats", "-s", action="store_true",
                    help="Statistik saja")
    ap.add_argument("--no-dedupe", action="store_true",
                    help="Jangan hapus duplikat")

    args = ap.parse_args()

    # Load
    data = load_slug_by_genre(args.input)
    if data is None:
        sys.exit(1)

    # Filter genre
    if args.genre:
        if args.genre in data:
            data = {args.genre: data[args.genre]}
        else:
            cprint(f"  ❌ Genre '{args.genre}' tidak ada", C.RED)
            print(f"  Tersedia: {', '.join(data.keys())}")
            sys.exit(1)

    # Extract
    extract_result = extract_slugs(data, dedupe=not args.no_dedupe)

    # Stats
    if args.stats:
        display_stats(data, extract_result)
        return

    # Actions
    if args.combined:
        display_stats(data, extract_result)
        print()
        out, count = save_flat(extract_result["all"], args.output)
        cprint(f"\n  ✅ Slugs all: {out} ({count})", C.GREEN)

        saved = save_by_genre(extract_result["by_genre"])
        cprint(f"  ✅ Per genre: {len(saved)} file", C.GREEN)

        combined = save_combined(
            extract_result["all"],
            {g: len(s) for g, s in extract_result["by_genre"].items()},
        )
        cprint(f"  ✅ Combined: {combined}", C.GREEN)

    elif args.by_genre:
        saved = save_by_genre(extract_result["by_genre"])
        cprint(f"\n  ✅ Saved {len(saved)} file di: {DEFAULT_OUTPUT_BY_GENRE}", C.GREEN)
        for genre, path, count in saved:
            print(f"     {genre:<25} {count:>4} slug")

    elif args.all:
        out, count = save_flat(extract_result["all"], args.output)
        cprint(f"\n  ✅ Saved: {out}", C.GREEN)
        print(f"     {count} slug")

    else:
        interactive_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⏸️  Interrupted\n")