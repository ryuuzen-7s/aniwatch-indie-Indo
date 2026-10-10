"""
analyzer_slug.py - Katalog slug di JSON (SLUG_N format).

Jalankan:
    python tools/analyzer_slug.py                        # menu interaktif
    python tools/analyzer_slug.py --input file.json      # custom input
    python tools/analyzer_slug.py --export               # DB -> JSON
    python tools/analyzer_slug.py --query a              # cari diawali 'a'
    python tools/analyzer_slug.py --stats                # statistik
    python tools/analyzer_slug.py --save-slugs           # simpan daftar slug ke data/base/
    python tools/analyzer_slug.py --change-json          # ganti JSON (path baru)
"""
import sys
import re
import json
import argparse
from datetime import datetime
from pathlib import Path
from collections import Counter

# ═══════════════════════════════════════════════════════════
#  PATH FIX
# ═══════════════════════════════════════════════════════════
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ROOT = _ROOT


# ═══════════════════════════════════════════════════════════
#  CONFIG — Paths
# ═══════════════════════════════════════════════════════════
BASE_DIR = ROOT / "data" / "base"
BASE_DIR.mkdir(parents=True, exist_ok=True)

# Config file untuk simpan pilihan default
CONFIG_FILE = BASE_DIR / ".slug_analyzer_config.json"

# Default input
DEFAULT_JSON = BASE_DIR / "dump" / "slug_by_genre.json"
DEFAULT_OUTPUT = BASE_DIR / "slug_catalog.json"


# ═══════════════════════════════════════════════════════════
#  CONFIG LOAD/SAVE (untuk ganti JSON)
# ═══════════════════════════════════════════════════════════
def load_config():
    """Load config dari file."""
    if not CONFIG_FILE.exists():
        return {"current_json": str(DEFAULT_JSON)}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"current_json": str(DEFAULT_JSON)}


def save_config(cfg):
    """Save config."""
    CONFIG_FILE.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


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
#  LOAD JSON (multi-format)
# ═══════════════════════════════════════════════════════════
def load_json(path):
    """
    Load JSON dengan auto-detect format.
    Return dict {SLUG_N: value} atau nested.
    """
    p = Path(path)
    if not p.exists():
        return {}

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        cprint(f"  ⚠️  Gagal baca: {e}", C.YELLOW)
        return {}

    result = {}

    # Format array
    if isinstance(data, list):
        for i, item in enumerate(data, 1):
            if isinstance(item, str):
                result[f"SLUG_{i}"] = item
            elif isinstance(item, dict):
                val = item.get("slug") or item.get("title") or str(item)
                result[f"SLUG_{i}"] = val
        return result

    if not isinstance(data, dict):
        return {}

    # Format flat (SLUG_N / GENRE_N)
    for k, v in data.items():
        if re.match(r"^(GENRE|SLUG|ITEM|ANIME)_\d+$", k) and isinstance(v, str):
            result[k] = v

    if result:
        return result

    # Format nested
    nested = False
    for k, v in data.items():
        if isinstance(v, dict) and ("animes" in v or "items" in v):
            nested = True
            break

    if nested:
        idx = 1
        seen = set()
        for genre_key, genre_data in data.items():
            animes = genre_data.get("animes") or genre_data.get("items") or []
            for item in animes:
                if isinstance(item, dict):
                    title = item.get("title") or item.get("slug") or ""
                elif isinstance(item, str):
                    title = item
                else:
                    continue

                if title and title not in seen:
                    seen.add(title)
                    result[f"SLUG_{idx}"] = title
                    idx += 1
        return result

    # Fallback: string value
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = v

    return result


# ═══════════════════════════════════════════════════════════
#  SAVE JSON
# ═══════════════════════════════════════════════════════════
def save_json(path, data):
    """Save JSON ke file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return p


# ═══════════════════════════════════════════════════════════
#  SAVE SLUGS ⭐ BARU
# ═══════════════════════════════════════════════════════════
def save_slugs(slugs, output_file=None, prefix="SLUG"):
    """
    Simpan daftar slug ke file JSON.
    Format: {"SLUG_1": "xxx", "SLUG_2": "yyy", ...}
    """
    section(f"💾 SIMPAN SLUG ({len(slugs)} slug)")

    output = Path(output_file) if output_file else DEFAULT_OUTPUT

    # Build output dengan prefix
    values = sorted(slugs.values())
    result = {f"{prefix}_{i}": v for i, v in enumerate(values, 1)}

    # Save
    save_json(output, result)

    cprint(f"  ✅ Tersimpan: {output}", C.GREEN)
    print(f"  📊 Total    : {len(result)} slug")
    print(f"  💾 Size     : {output.stat().st_size:,} bytes")

    # Preview
    print()
    print("  Preview 10:")
    for i, (k, v) in enumerate(list(result.items())[:10], 1):
        print(f"    {k:<12} = {v}")

    if len(result) > 10:
        print(f"    ... dan {len(result) - 10} lagi")

    return output


# ═══════════════════════════════════════════════════════════
#  CHANGE JSON ⭐ BARU
# ═══════════════════════════════════════════════════════════
def change_json(new_path):
    """
    Ganti default JSON.
    Simpan ke config file.
    """
    new_path = Path(new_path)

    if not new_path.exists():
        cprint(f"  ❌ File tidak ada: {new_path}", C.RED)
        return False

    # Cek valid JSON
    try:
        json.loads(new_path.read_text(encoding="utf-8"))
    except Exception as e:
        cprint(f"  ❌ Bukan JSON valid: {e}", C.RED)
        return False

    # Save config
    cfg = load_config()
    old_path = cfg.get("current_json", "-")
    cfg["current_json"] = str(new_path)
    cfg["changed_at"] = datetime.now().isoformat()
    save_config(cfg)

    section("🔄 GANTI JSON")
    print(f"  📁 Sebelum : {old_path}")
    print(f"  📁 Sesudah : {new_path}")
    cprint(f"  ✅ Config tersimpan: {CONFIG_FILE}", C.GREEN)

    return True


def get_current_json():
    """Ambil path JSON saat ini."""
    cfg = load_config()
    current = cfg.get("current_json", str(DEFAULT_JSON))
    return Path(current)


# ═══════════════════════════════════════════════════════════
#  EXPORT FROM DB
# ═══════════════════════════════════════════════════════════
def export_from_db(output_path=None):
    """Export slug dari DB ke JSON."""
    section("📤 EXPORT DB → JSON")

    try:
        from sqlalchemy import select
        from db import get_session
        from db.models import Anime
    except ImportError as e:
        cprint(f"  ❌ Import error: {e}", C.RED)
        return

    with get_session() as s:
        animes = list(s.execute(select(Anime).order_by(Anime.slug)).scalars())

    if not animes:
        cprint("  ⚠️  Tidak ada anime di DB", C.YELLOW)
        return

    # Build dict
    slugs = {}
    for i, a in enumerate(animes, 1):
        if a.slug:
            slugs[f"SLUG_{i}"] = a.slug

    # Save
    output = Path(output_path) if output_path else DEFAULT_OUTPUT
    save_json(output, slugs)

    print(f"  📊 Anime     : {len(animes)}")
    print(f"  ✅ Tersimpan : {output}")
    print(f"  💾 Size      : {output.stat().st_size:,} bytes")

    # Preview
    print()
    print("  Preview 10:")
    for i, (k, v) in enumerate(list(slugs.items())[:10], 1):
        print(f"    {k:<12} = {v}")


# ═══════════════════════════════════════════════════════════
#  QUERY
# ═══════════════════════════════════════════════════════════
def find_slugs(slugs, mode="starts", value="a"):
    """Cari slug."""
    results = []
    value_lower = value.lower()

    for key, slug in slugs.items():
        slug_lower = slug.lower()
        match = False

        if mode == "starts":
            match = slug_lower.startswith(value_lower)
        elif mode == "ends":
            match = slug_lower.endswith(value_lower)
        elif mode == "contains":
            match = value_lower in slug_lower
        elif mode == "pattern":
            pattern = value_lower.replace("*", ".*")
            try:
                match = re.match(pattern + "$", slug_lower) is not None
            except re.error:
                pass

        if match:
            results.append((key, slug))

    return results


def display_results(results, query_info=""):
    """Tampilkan hasil query."""
    if not results:
        cprint("  (tidak ada slug yang cocok)", C.YELLOW)
        return

    section(f"🔍 HASIL: {query_info} — {len(results)} slug")

    print(f"  {'KEY':<12} {'SLUG'}")
    cprint("  " + "-" * 60, C.DIM)

    for key, slug in results:
        print(f"  {C.CYAN}{key:<12}{C.RESET} {slug}")


# ═══════════════════════════════════════════════════════════
#  STATISTIK
# ═══════════════════════════════════════════════════════════
def show_stats(slugs, json_path):
    """Statistik slug."""
    section("📊 STATISTIK SLUG")

    if not slugs:
        cprint("  ⚠️  JSON kosong", C.YELLOW)
        print(f"  📁 File: {json_path}")
        return

    values = list(slugs.values())
    total = len(values)
    avg_len = sum(len(v) for v in values) / total if total else 0

    print(f"  📁 File           : {json_path}")
    print(f"  📊 Total slug     : {total}")
    print(f"  📏 Rata-rata len  : {avg_len:.1f} char")

    # Prefix distribution
    prefixes = Counter(v[0].lower() for v in values if v)
    print()
    print("  Distribusi huruf awal:")
    for letter, count in prefixes.most_common(10):
        bar = "█" * min(count, 40)
        print(f"    {letter} : {count:<5} {C.GREEN}{bar}{C.RESET}")

    # Suffix distribution
    suffixes = Counter(v[-3:].lower() for v in values if len(v) >= 3)
    if suffixes:
        print()
        print("  Suffix (3 char akhir):")
        for suffix, count in suffixes.most_common(10):
            bar = "█" * min(count, 40)
            print(f"    {suffix} : {count:<5} {C.GREEN}{bar}{C.RESET}")

    # Preview
    print()
    print("  Preview 10:")
    for i, (k, v) in enumerate(sorted(slugs.items())[:10], 1):
        print(f"    {k:<12} = {v}")


# ═══════════════════════════════════════════════════════════
#  MENU INTERAKTIF
# ═══════════════════════════════════════════════════════════
MENU = """
╔══════════════════════════════════════════════════════════════╗
║           🔍 ANALYZER SLUG - JSON Catalog                    ║
╠══════════════════════════════════════════════════════════════╣
║  QUERY                                                       ║
║    [1] Cari diawali                                          ║
║    [2] Cari diakhiri                                         ║
║    [3] Cari mengandung                                       ║
║    [4] Cari pola (wildcard *)                                ║
║                                                              ║
║  ANALYZER                                                    ║
║    [5] 📊 Statistik                                          ║
║    [6] 📄 Lihat isi file                                     ║
║                                                              ║
║  SAVE / CHANGE ⭐                                            ║
║    [7] 💾 Simpan slug ke data/base/                          ║
║    [8] 🔄 Ganti JSON                                         ║
║    [9] 📤 Export DB → JSON                                   ║
║                                                              ║
║    [0] Keluar                                                ║
╚══════════════════════════════════════════════════════════════╝
"""


def ask_text(prompt, default=""):
    if default:
        val = input(f"  {prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"  {prompt}: ").strip()


def interactive_menu():
    while True:
        current_json = get_current_json()
        slugs = load_json(current_json)

        section("🔍 ANALYZER SLUG")
        print()
        print(f"  📁 JSON  : {current_json}")
        print(f"  📊 Total : {len(slugs)} slug")
        print(f"  📁 Output: {BASE_DIR}")
        print(MENU)

        choice = input(f"  {C.CYAN}Pilih: {C.RESET}").strip()

        try:
            if choice == "0":
                cprint("\n  👋 Bye!", C.CYAN)
                break

            elif choice == "1":
                q = input("  Diawali: ").strip()
                if q:
                    display_results(find_slugs(slugs, "starts", q),
                                    f"diawali '{q}'")

            elif choice == "2":
                q = input("  Diakhiri: ").strip()
                if q:
                    display_results(find_slugs(slugs, "ends", q),
                                    f"diakhiri '{q}'")

            elif choice == "3":
                q = input("  Mengandung: ").strip()
                if q:
                    display_results(find_slugs(slugs, "contains", q),
                                    f"mengandung '{q}'")

            elif choice == "4":
                q = input("  Pola (mis. '*-sub-indo'): ").strip()
                if q:
                    display_results(find_slugs(slugs, "pattern", q),
                                    f"pola '{q}'")

            elif choice == "5":
                show_stats(slugs, current_json)

            elif choice == "6":
                section("📄 ISI FILE")
                if current_json.exists():
                    print()
                    print(current_json.read_text(encoding="utf-8"))
                else:
                    cprint(f"  ❌ File tidak ada: {current_json}", C.RED)

            elif choice == "7":
                if not slugs:
                    cprint("  ⚠️  Tidak ada slug untuk disimpan", C.YELLOW)
                else:
                    out = ask_text("Output file", str(DEFAULT_OUTPUT))
                    save_slugs(slugs, output_file=out)

            elif choice == "8":
                section("🔄 GANTI JSON")
                print(f"  JSON saat ini: {current_json}")
                print()
                new_path = ask_text("Path JSON baru", "")
                if new_path:
                    change_json(new_path)

            elif choice == "9":
                export_from_db()

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
        description="Analisa slug JSON",
    )
    ap.add_argument("--input", "-i", type=str, default=None,
                    help="Path JSON input (default: dari config)")
    ap.add_argument("--query", "-q", type=str, help="Cari diawali")
    ap.add_argument("--contains", "-c", type=str, help="Cari mengandung")
    ap.add_argument("--ends", type=str, help="Cari diakhiri")
    ap.add_argument("--pattern", "-p", type=str, help="Pola wildcard")
    ap.add_argument("--stats", "-s", action="store_true", help="Statistik")
    ap.add_argument("--show", action="store_true", help="Tampilkan file")
    ap.add_argument("--export", "-e", action="store_true",
                    help="Export DB → JSON")
    ap.add_argument("--save-slugs", action="store_true",
                    help="Simpan slug ke data/base/slug_catalog.json")
    ap.add_argument("--save-output", type=str, default=None,
                    help="Custom output untuk --save-slugs")
    ap.add_argument("--change-json", type=str, default=None,
                    help="Ganti default JSON ke path ini")

    args = ap.parse_args()

    # Handle --change-json
    if args.change_json:
        change_json(args.change_json)
        return

    # Tentukan input path
    current_json = Path(args.input) if args.input else get_current_json()

    # Handle --export
    if args.export:
        export_from_db(args.input)
        return

    # Load JSON
    slugs = load_json(current_json)

    # Handle --save-slugs
    if args.save_slugs:
        if not slugs:
            cprint(f"  ⚠️  JSON kosong: {current_json}", C.YELLOW)
            return
        save_slugs(slugs, output_file=args.save_output)
        return

    # Query modes
    if args.query:
        display_results(find_slugs(slugs, "starts", args.query),
                        f"diawali '{args.query}'")
    elif args.contains:
        display_results(find_slugs(slugs, "contains", args.contains),
                        f"mengandung '{args.contains}'")
    elif args.ends:
        display_results(find_slugs(slugs, "ends", args.ends),
                        f"diakhiri '{args.ends}'")
    elif args.pattern:
        display_results(find_slugs(slugs, "pattern", args.pattern),
                        f"pola '{args.pattern}'")
    elif args.stats:
        show_stats(slugs, current_json)
    elif args.show:
        section("📄 ISI FILE")
        if current_json.exists():
            print()
            print(current_json.read_text(encoding="utf-8"))
        else:
            cprint(f"  ❌ File tidak ada: {current_json}", C.RED)
    else:
        interactive_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted\n")