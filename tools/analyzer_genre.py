"""
analyzer_genre.py - Analisa genre dari JSON, split by abjad.

Jalankan:
    python analyzer_genre.py                              # menu interaktif
    python analyzer_genre.py --input data/genre.json      # custom JSON
    python analyzer_genre.py --split                      # split A-Z
    python analyzer_genre.py --letter A                   # tampilkan segmen 'A'
    python analyzer_genre.py --export                     # DB -> JSON
    python analyzer_genre.py --stats
"""
import sys
import re
import json
import argparse
from collections import Counter
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from sqlalchemy import select
from pathlib import Path
import sys
# ═══════════════════════════════════════════════════════════
#  PATH FIX — supaya bisa import dari root project
# ═══════════════════════════════════════════════════════════
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# ═══════════════════════════════════════════════════════════

from db import get_session
from db.models import Anime


# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
DEFAULT_JSON = Path(__file__).parent / "data" / "base" / "genre_catalog.json"
SPLIT_DIR = Path(__file__).parent / "data" / "base" / "genre_split"


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
#  JSON MANAGER
# ═══════════════════════════════════════════════════════════
def load_json(path):
    """
    Load JSON dengan auto-detect format.

    Format 1 - flat GENRE_N:
        {"GENRE_1": "Action", "GENRE_2": "Romance"}

    Format 2 - flat SLUG_N:
        {"SLUG_1": "naruto", "SLUG_2": "one-piece"}

    Format 3 - nested (dari scraper_by_genre.py):
        {"action": {"animes": [{"slug": "xxx", "title": "yyy"}]}}

    Format 4 - array:
        [{"slug": "xxx", "title": "yyy"}]
    """
    p = Path(path)
    if not p.exists():
        return {}

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        cprint(f"  WARN Gagal baca JSON: {e}", C.YELLOW)
        return {}

    result = {}

    # Format 4: Array
    if isinstance(data, list):
        for i, item in enumerate(data, 1):
            if isinstance(item, str):
                result[f"ITEM_{i}"] = item
            elif isinstance(item, dict):
                val = item.get("title") or item.get("slug") or item.get("name") or str(item)
                result[f"ITEM_{i}"] = val
        return result

    if not isinstance(data, dict):
        return {}

    # Format 1 & 2: Flat GENRE_N / SLUG_N
    for k, v in data.items():
        if re.match(r"^(GENRE|SLUG|ITEM|ANIME)_\d+$", k) and isinstance(v, str):
            result[k] = v

    if result:
        return result

    # Format 3: Nested - cek dulu
    nested_format = False
    for k, v in data.items():
        if isinstance(v, dict) and ("animes" in v or "items" in v):
            nested_format = True
            break

    if nested_format:
        idx = 1
        seen_titles = set()
        for genre_key, genre_data in data.items():
            animes = genre_data.get("animes") or genre_data.get("items") or []
            for item in animes:
                if isinstance(item, str):
                    title = item
                elif isinstance(item, dict):
                    title = item.get("title") or item.get("slug") or ""
                else:
                    continue

                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)

                # Format: "Title" (tanpa prefix genre biar rapi)
                result[f"ANIME_{idx}"] = title
                idx += 1
        return result

    # Fallback: semua string value
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = v

    return result

def save_json(path, data):
    """Save JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_genre_by_value(genres, value):
    """Cari key dari value (case-insensitive)."""
    value_lower = value.lower()
    for k, v in genres.items():
        if v.lower() == value_lower:
            return k
    return None


def get_next_id(genres):
    """ID berikutnya."""
    if not genres:
        return 1
    nums = []
    for k in genres.keys():
        m = re.match(r"^(?:GENRE|SLUG)_(\d+)$", k)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


def add_genre(genres, value):
    """Tambah genre."""
    if get_genre_by_value(genres, value):
        return None
    next_id = get_next_id(genres)
    key = f"GENRE_{next_id}"
    genres[key] = value
    return key


def remove_genre(genres, value):
    """Hapus genre."""
    key = get_genre_by_value(genres, value)
    if key:
        del genres[key]
        return True
    return False


def reindex(genres):
    """Reindex: GENRE_1, GENRE_2, ... urut alfabet."""
    # Detect prefix yang dipakai
    prefix = "GENRE"
    for k in genres.keys():
        if k.startswith("SLUG_"):
            prefix = "SLUG"
            break

    values = sorted(genres.values(), key=lambda x: x.lower())
    return {f"{prefix}_{i}": v for i, v in enumerate(values, 1)}


# ═══════════════════════════════════════════════════════════
#  SPLIT BY ALPHABET
# ═══════════════════════════════════════════════════════════
def split_by_alphabet(genres, output_dir=None):
    """
    Bagi genre berdasarkan huruf awal.

    Format: {"GENRE_1": "Action", ...} → 
            [{"letter": "A", "count": 5, "items": [...]}, ...]
    """
    buckets = {}

    for key, value in genres.items():
        if not value:
            continue
        first = value[0].upper()
        if not first.isalpha():
            first = "#"  # simbol/angka
        buckets.setdefault(first, []).append({
            "key": key,
            "value": value,
        })

    # Sort by letter
    sorted_letters = sorted(buckets.keys(), key=lambda x: (x == "#", x))

    result = []
    for letter in sorted_letters:
        items = sorted(buckets[letter], key=lambda x: x["value"].lower())
        result.append({
            "letter": letter,
            "count": len(items),
            "items": items,
        })

    # Save per segmen
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        for segment in result:
            letter = segment["letter"]
            # Nama file: segmen_A.json, segmen_B.json, segmen_sym.json
            fname = f"segmen_{letter}.json" if letter.isalpha() else "segmen_symbol.json"

            segment_data = {
                "letter": letter,
                "count": segment["count"],
                "items": {
                    f"{letter}_{i}": item["value"]
                    for i, item in enumerate(segment["items"], 1)
                },
            }
            (out / fname).write_text(
                json.dumps(segment_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    return result


def display_split(result, show_items=True):
    """Tampilkan hasil split."""
    if not result:
        cprint("  (tidak ada data)", C.YELLOW)
        return

    total = sum(s["count"] for s in result)
    print(f"  Total: {total} item di {len(result)} segmen")
    print()

    # Tabel ringkasan
    print(f"  {'SEGMEN':<10} {'JUMLAH':<8} BAR")
    cprint("  " + "-" * 60, C.DIM)

    max_count = max(s["count"] for s in result) if result else 0

    for segment in result:
        letter = segment["letter"]
        count = segment["count"]
        bar_len = int(count / max_count * 40) if max_count else 0
        bar = "█" * bar_len

        print(f"  {letter:<10} {count:<8} {C.GREEN}{bar}{C.RESET}")

    # Detail per segmen
    if show_items:
        for segment in result:
            letter = segment["letter"]
            print()
            cprint(f"  ── Segmen '{letter}' ({segment['count']} item) ──", C.CYAN)

            for i, item in enumerate(segment["items"], 1):
                print(f"    {i:>3}. [{item['key']:<10}] {item['value']}")


# ═══════════════════════════════════════════════════════════
#  EXPORT FROM DB
# ═══════════════════════════════════════════════════════════
def export_from_db(output_path=None):
    """Export genre dari DB ke JSON."""
    section("📤 EXPORT DB → JSON")

    with get_session() as s:
        animes = list(s.execute(select(Anime)).scalars())

    if not animes:
        cprint("  ⚠️  Tidak ada anime di DB", C.YELLOW)
        return

    # Kumpulkan genre unik
    genre_counter = Counter()
    for a in animes:
        for g in (a.genres or []):
            if g and isinstance(g, str):
                genre_counter[g.strip()] += 1

    if not genre_counter:
        cprint("  ⚠️  Tidak ada genre", C.YELLOW)
        return

    print(f"  📊 Total anime    : {len(animes)}")
    print(f"  📊 Genre unik     : {len(genre_counter)}")

    # Build JSON
    genres = {}
    for i, genre in enumerate(sorted(genre_counter.keys(), key=lambda x: x.lower()), 1):
        genres[f"GENRE_{i}"] = genre

    # Save
    out = Path(output_path) if output_path else DEFAULT_JSON
    save_json(out, genres)

    print()
    print(f"  ✅ Tersimpan      : {len(genres)} genre")
    print(f"  📁 File           : {out}")

    # Preview
    print()
    print("  Preview (top 10 by frekuensi):")
    for genre, count in genre_counter.most_common(10):
        key = get_genre_by_value(genres, genre)
        print(f"    {key:<12} {genre:<25} {count:>4}x")


# ═══════════════════════════════════════════════════════════
#  STATISTIK
# ═══════════════════════════════════════════════════════════
def show_stats(genres, json_path):
    """Statistik genre."""
    section("📊 STATISTIK GENRE")

    if not genres:
        cprint("  ⚠️  JSON kosong", C.YELLOW)
        print(f"  📁 File: {json_path}")
        return

    values = list(genres.values())

    print(f"  📁 File           : {json_path}")
    print(f"  📊 Total genre    : {len(genres)}")

    # Panjang rata-rata
    avg_len = sum(len(v) for v in values) / len(values)
    print(f"  📏 Rata-rata len  : {avg_len:.1f} char")

    # Range key
    nums = [int(k.split("_")[1]) for k in genres.keys() if "_" in k]
    if nums:
        prefix = genres.keys().__iter__().__next__().split("_")[0]
        print(f"  🔑 Key range      : {prefix}_{min(nums)} - {prefix}_{max(nums)}")

    # Distribusi huruf
    letters = Counter(v[0].upper() for v in values if v)
    print()
    print("  Distribusi huruf awal:")
    for letter, count in letters.most_common():
        bar = "█" * min(count, 40)
        print(f"    {letter} : {count:<5} {C.GREEN}{bar}{C.RESET}")


# ═══════════════════════════════════════════════════════════
#  SHOW FILE
# ═══════════════════════════════════════════════════════════
def show_file(json_path):
    """Tampilkan isi file."""
    section("📄 ISI FILE JSON")

    p = Path(json_path)
    if not p.exists():
        cprint(f"  ⚠️  File tidak ada: {json_path}", C.YELLOW)
        return

    print(f"  📁 Path: {p}")
    print(f"  📏 Size: {p.stat().st_size} bytes")
    print()
    print("  " + "-" * 60)
    print(p.read_text(encoding="utf-8"))
    print("  " + "-" * 60)


# ═══════════════════════════════════════════════════════════
#  LIST SEGMEN FILES
# ═══════════════════════════════════════════════════════════
def list_segments(split_dir):
    """List segmen file yang sudah dibuat."""
    section("📂 SEGMEN FILES")

    d = Path(split_dir)
    if not d.exists():
        cprint(f"  ⚠️  Folder tidak ada: {d}", C.YELLOW)
        print(f"  💡 Jalankan: python analyzer_genre.py --split")
        return

    files = sorted(d.glob("segmen_*.json"))
    if not files:
        cprint("  (belum ada segmen file)", C.YELLOW)
        return

    print(f"  📁 Folder: {d}")
    print(f"  📊 Total : {len(files)} file")
    print()
    print(f"  {'FILE':<25} {'SIZE':>10} {'COUNT':>8}")
    cprint("  " + "-" * 50, C.DIM)

    for f in files:
        size = f.stat().st_size
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            count = data.get("count", 0)
        except Exception:
            count = 0
        print(f"  {f.name:<25} {size:>10} {count:>8}")


# ═══════════════════════════════════════════════════════════
#  INTERACTIVE MENU
# ═══════════════════════════════════════════════════════════
def ask_text(prompt, default=""):
    if default:
        val = input(f"  {prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"  {prompt}: ").strip()


def interactive_menu():
    # Default path
    current_json = str(DEFAULT_JSON)

    while True:
        genres = load_json(current_json)

        section("🎭 ANALYZER GENRE")
        print()
        print(f"  📁 JSON  : {current_json}")
        print(f"  📊 Total : {len(genres)} genre")
        print()
        print("  QUERY:")
        print("    [1] Cari diawali")
        print("    [2] Cari diakhiri")
        print("    [3] Cari mengandung")
        print("    [4] Cari pola (wildcard *)")
        print()
        print("  SPLIT BY ALPHABET:")
        print("    [5] Split & save segmen A-Z")
        print("    [6] Tampilkan segmen")
        print("    [7] Lihat segmen tertentu")
        print("    [8] List segmen files")
        print()
        print("  MANAGE:")
        print("    [9]  Ganti input JSON")
        print("    [10] Export DB → JSON")
        print("    [11] Tambah genre")
        print("    [12] Hapus genre")
        print("    [13] Statistik")
        print("    [14] Lihat isi file")
        print()
        print("    [0] Keluar")

        choice = input(f"\n  {C.CYAN}Pilih: {C.RESET}").strip()

        try:
            if choice == "0":
                cprint("\n  👋 Bye!", C.CYAN)
                break

            elif choice == "1":
                q = input("  Diawali: ").strip()
                if q:
                    results = [(k, v) for k, v in genres.items()
                               if v.lower().startswith(q.lower())]
                    _display_query(results, f"diawali '{q}'")

            elif choice == "2":
                q = input("  Diakhiri: ").strip()
                if q:
                    results = [(k, v) for k, v in genres.items()
                               if v.lower().endswith(q.lower())]
                    _display_query(results, f"diakhiri '{q}'")

            elif choice == "3":
                q = input("  Mengandung: ").strip()
                if q:
                    results = [(k, v) for k, v in genres.items()
                               if q.lower() in v.lower()]
                    _display_query(results, f"mengandung '{q}'")

            elif choice == "4":
                q = input("  Pola (mis. '*a*'): ").strip()
                if q:
                    pattern = q.lower().replace("*", ".*")
                    results = [(k, v) for k, v in genres.items()
                               if re.match(pattern + "$", v.lower())]
                    _display_query(results, f"pola '{q}'")

            elif choice == "5":
                if not genres:
                    cprint("  ⚠️  JSON kosong", C.YELLOW)
                else:
                    result = split_by_alphabet(genres, output_dir=SPLIT_DIR)
                    cprint(f"  ✅ Split selesai: {len(result)} segmen", C.GREEN)
                    print(f"  📁 Folder: {SPLIT_DIR}")
                    display_split(result, show_items=False)

            elif choice == "6":
                if not genres:
                    cprint("  ⚠️  JSON kosong", C.YELLOW)
                else:
                    result = split_by_alphabet(genres)
                    display_split(result, show_items=True)

            elif choice == "7":
                letter = input("  Huruf (A-Z): ").strip().upper()
                if letter and genres:
                    result = split_by_alphabet(genres)
                    segment = next((s for s in result if s["letter"] == letter), None)
                    if segment:
                        cprint(f"\n  ── Segmen '{letter}' ({segment['count']} item) ──", C.CYAN)
                        for i, item in enumerate(segment["items"], 1):
                            print(f"    {i:>3}. [{item['key']:<10}] {item['value']}")
                    else:
                        cprint(f"  ⚠️  Segmen '{letter}' tidak ada", C.YELLOW)

            elif choice == "8":
                list_segments(SPLIT_DIR)

            elif choice == "9":
                new_path = ask_text("Path JSON baru", current_json)
                if new_path:
                    current_json = new_path
                    cprint(f"  ✅ Path diubah: {current_json}", C.GREEN)

            elif choice == "10":
                export_from_db(current_json)

            elif choice == "11":
                g = input("  Genre baru: ").strip()
                if g:
                    key = add_genre(genres, g)
                    if not key:
                        cprint(f"  ⚠️  Sudah ada", C.YELLOW)
                    else:
                        genres = reindex(genres)
                        save_json(current_json, genres)
                        cprint(f"  ✅ Ditambahkan", C.GREEN)

            elif choice == "12":
                g = input("  Genre hapus: ").strip()
                if g:
                    if remove_genre(genres, g):
                        genres = reindex(genres)
                        save_json(current_json, genres)
                        cprint(f"  ✅ Dihapus", C.GREEN)
                    else:
                        cprint(f"  ⚠️  Tidak ditemukan", C.YELLOW)

            elif choice == "13":
                show_stats(genres, current_json)

            elif choice == "14":
                show_file(current_json)

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


def _display_query(results, info):
    """Display hasil query."""
    section(f"🔍 HASIL: {info} — {len(results)} item")

    if not results:
        cprint("  (tidak ada)", C.YELLOW)
        return

    print(f"  {'KEY':<12} {'VALUE'}")
    cprint("  " + "-" * 40, C.DIM)
    for k, v in sorted(results):
        print(f"  {C.CYAN}{k:<12}{C.RESET} {v}")


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(
        description="Analisa genre JSON + split by alphabet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python analyzer_genre.py                              # menu
  python analyzer_genre.py --input data/genre.json      # custom JSON
  python analyzer_genre.py --split                      # split A-Z
  python analyzer_genre.py --letter A                   # tampilkan 'A'
  python analyzer_genre.py --list-segments              # list files
  python analyzer_genre.py --export                     # DB -> JSON
  python analyzer_genre.py --stats
  python analyzer_genre.py --show
""",
    )
    ap.add_argument("--input", "-i", type=str, default=str(DEFAULT_JSON),
                    help=f"Path JSON (default: {DEFAULT_JSON})")
    ap.add_argument("--split", action="store_true",
                    help="Split by alphabet + save segmen files")
    ap.add_argument("--letter", type=str, help="Tampilkan segmen 1 huruf")
    ap.add_argument("--list-segments", action="store_true",
                    help="List segmen files")
    ap.add_argument("--export", "-e", action="store_true",
                    help="Export DB → JSON")
    ap.add_argument("--stats", "-s", action="store_true",
                    help="Statistik")
    ap.add_argument("--show", action="store_true",
                    help="Tampilkan isi file")

    args = ap.parse_args()

    # Export
    if args.export:
        export_from_db(args.input)
        return

    # Load JSON
    genres = load_json(args.input)

    # List segments
    if args.list_segments:
        list_segments(SPLIT_DIR)
        return

    # Split
    if args.split:
        if not genres:
            cprint(f"  ⚠️  JSON kosong: {args.input}", C.YELLOW)
            return
        result = split_by_alphabet(genres, output_dir=SPLIT_DIR)
        cprint(f"  ✅ Split: {len(result)} segmen", C.GREEN)
        display_split(result, show_items=False)
        print()
        cprint(f"  📁 Saved to: {SPLIT_DIR}", C.GREEN)
        return

    # Letter
    if args.letter:
        letter = args.letter.upper()
        result = split_by_alphabet(genres)
        segment = next((s for s in result if s["letter"] == letter), None)
        if segment:
            section(f"📚 SEGMEN '{letter}' ({segment['count']} item)")
            for i, item in enumerate(segment["items"], 1):
                print(f"  {i:>3}. [{item['key']:<10}] {item['value']}")
        else:
            cprint(f"  ⚠️  Segmen '{letter}' tidak ada", C.YELLOW)
        return

    # Stats
    if args.stats:
        show_stats(genres, args.input)
        return

    # Show
    if args.show:
        show_file(args.input)
        return

    # Menu
    interactive_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted\n")