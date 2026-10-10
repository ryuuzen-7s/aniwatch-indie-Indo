"""
add_env.py - Edit .env berdasarkan JSON dari data/base/slugs/.

Jalankan:
    python tools/add_env.py                     # menu interaktif
    python tools/add_env.py --list              # list JSON di slugs/
    python tools/add_env.py --preview           # preview saja
    python tools/add_env.py --select 1          # pilih file index ke-1
    python tools/add_env.py --input FILE        # custom input
    python tools/add_env.py --key SLUG          # prefix key
    python tools/add_env.py --merge             # merge, bukan replace
    python tools/add_env.py --yes               # tanpa konfirmasi
"""
import sys
import re
import json
import argparse
import shutil
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
#  CONFIG — Paths
# ═══════════════════════════════════════════════════════════
SLUGS_DIR = ROOT / "data" / "base" / "slugs"
BACKUP_DIR = ROOT / "backup" / "env_backup"
DEFAULT_ENV = ROOT / ".env"

SLUGS_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


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
#  FIND JSON FILES (recursive di slugs/)
# ═══════════════════════════════════════════════════════════
def find_json_files(base_dir=None):
    """
    Cari semua file .json di data/base/slugs/ (recursive).

    Return: list of dict {
        "path": Path,
        "name": str,
        "rel": str (relative to slugs_dir),
        "size": int,
        "count": int (jumlah item di JSON)
    }
    """
    base = Path(base_dir) if base_dir else SLUGS_DIR

    if not base.exists():
        return []

    files = []

    for f in sorted(base.rglob("*.json")):
        if not f.is_file():
            continue

        try:
            size = f.stat().st_size
            rel = f.relative_to(base)

            # Hitung item
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    count = len(data)
                elif isinstance(data, list):
                    count = len(data)
                else:
                    count = 0
            except Exception:
                count = 0

            files.append({
                "path": f,
                "name": f.name,
                "rel": str(rel),
                "size": size,
                "count": count,
            })
        except Exception:
            continue

    return files


def display_json_files(files):
    """Tampilkan list JSON files."""
    if not files:
        cprint("  (tidak ada file JSON)", C.YELLOW)
        return

    print()
    print(f"  {'#':<4} {'FILE':<40} {'ITEM':>6} {'SIZE':>10}")
    cprint("  " + "-" * 66, C.DIM)

    for i, f in enumerate(files, 1):
        rel = f["rel"][:38]
        item_str = str(f["count"])
        size_str = f"{f['size']:>8,} B"
        print(f"  {i:<4} {rel:<40} {item_str:>6} {size_str:>10}")


def select_json_file(files):
    """
    Pilih file JSON dari list.

    Return: Path atau None
    """
    if not files:
        return None

    # Kalau cuma 1 file → langsung pakai
    if len(files) == 1:
        cprint(f"\n  ℹ️  Hanya ada 1 file: {files[0]['rel']}", C.DIM)
        return files[0]["path"]

    # Kalau banyak → tanya user
    display_json_files(files)

    print()
    print(f"  📁 {len(files)} file ditemukan")
    print(f"  💡 Ketik angka (1-{len(files)}) untuk pilih")
    print(f"  💡 Ketik 'a' atau Enter untuk semua (gabung)")
    print(f"  💡 Ketik 'q' untuk batal")

    while True:
        try:
            choice = input(f"\n  {C.CYAN}Pilih: {C.RESET}").strip().lower()

            if not choice or choice in ("a", "all", "semua"):
                # Gabung semua → return list
                return [f["path"] for f in files]

            if choice in ("q", "quit", "exit", "0"):
                return None

            # Coba parse angka
            num = int(choice)
            if 1 <= num <= len(files):
                return files[num - 1]["path"]

            cprint(f"  ⚠️  Pilih 1-{len(files)} atau 'a'/'q'", C.YELLOW)

        except ValueError:
            cprint(f"  ⚠️  Input tidak valid", C.YELLOW)
        except KeyboardInterrupt:
            print()
            return None


# ═══════════════════════════════════════════════════════════
#  LOAD JSON (multi-format)
# ═══════════════════════════════════════════════════════════
def load_json(path):
    """Load JSON dengan auto-detect format."""
    p = Path(path)
    if not p.exists():
        return []

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        cprint(f"  ⚠️  Gagal baca {p.name}: {e}", C.YELLOW)
        return []

    items = []

    # Format 4: Array
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                items.append({"value": item, "meta": {}})
            elif isinstance(item, dict):
                items.append({
                    "value": item.get("slug") or item.get("title") or str(item),
                    "title": item.get("title", ""),
                    "meta": item,
                })
        return items

    if not isinstance(data, dict):
        return []

    # Format 1 & 2: Flat
    flat_found = False
    for k, v in data.items():
        if re.match(r"^(GENRE|SLUG|ITEM|ANIME)_\d+$", k) and isinstance(v, str):
            items.append({"value": v, "key": k, "meta": {}})
            flat_found = True

    if flat_found:
        def num_key(item):
            m = re.search(r"_(\d+)$", item.get("key", "0"))
            return int(m.group(1)) if m else 0
        items.sort(key=num_key)
        return items

    # Format 3: Nested
    nested_found = False
    for k, v in data.items():
        if isinstance(v, dict) and ("animes" in v or "items" in v):
            nested_found = True
            break

    if nested_found:
        seen = set()
        for genre_key, genre_data in data.items():
            animes = genre_data.get("animes") or genre_data.get("items") or []
            for item in animes:
                if isinstance(item, str):
                    slug = item
                    title = item
                elif isinstance(item, dict):
                    slug = item.get("slug") or ""
                    title = item.get("title") or slug
                else:
                    continue

                if not slug or slug in seen:
                    continue
                seen.add(slug)

                items.append({
                    "value": slug,
                    "title": title,
                    "genre": genre_key,
                    "meta": item if isinstance(item, dict) else {},
                })
        return items

    # Fallback
    for k, v in data.items():
        if isinstance(v, str):
            items.append({"value": v, "key": k, "meta": {}})

    return items


def load_multiple_jsons(paths):
    """Load multiple JSON files, gabung."""
    all_items = []
    seen = set()

    for path in paths:
        items = load_json(path)
        for item in items:
            val = item["value"]
            if val not in seen:
                seen.add(val)
                all_items.append(item)

    return all_items


# ═══════════════════════════════════════════════════════════
#  ENV PARSER / WRITER
# ═══════════════════════════════════════════════════════════
def parse_env(path):
    p = Path(path)
    if not p.exists():
        return [], {}

    lines = p.read_text(encoding="utf-8").split("\n")
    env_vars = {}

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip()

    return lines, env_vars


def write_env(path, lines):
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def backup_env(path, backup_dir=None):
    if not Path(path).exists():
        return None

    bd = Path(backup_dir) if backup_dir else BACKUP_DIR
    bd.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{Path(path).name}.{ts}.bak"
    backup_path = bd / backup_name

    shutil.copy2(path, backup_path)
    return backup_path


# ═══════════════════════════════════════════════════════════
#  UPDATE ENV
# ═══════════════════════════════════════════════════════════
def update_env(env_path, items, key_prefix="SLUG", mode="replace"):
    """
    Update .env dengan list item.
    Return: (added, updated, removed)
    """
    env_path = Path(env_path)

    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").split("\n")
    else:
        lines = []

    pattern = re.compile(rf"^{key_prefix}_(\d+)\s*=")

    existing_indices = []
    existing_values = {}

    for line in lines:
        m = pattern.match(line.strip())
        if m:
            idx = int(m.group(1))
            existing_indices.append(idx)
            val = line.split("=", 1)[1].strip()
            existing_values[val] = idx

    # Mode: replace
    if mode == "replace":
        new_lines = [line for line in lines if not pattern.match(line.strip())]

        added = 0
        for i, item in enumerate(items, 1):
            value = item["value"]
            new_lines.append(f"{key_prefix}_{i}={value}")
            added += 1

        write_env(env_path, new_lines)
        return added, 0, len(existing_indices)

    # Mode: merge
    elif mode == "merge":
        max_idx = max(existing_indices) if existing_indices else 0
        added = 0
        existing_values_set = set(existing_values.keys())
        new_lines = []

        for item in items:
            value = item["value"]
            if value in existing_values_set:
                continue
            max_idx += 1
            new_lines.append(f"{key_prefix}_{max_idx}={value}")
            added += 1
            existing_values_set.add(value)

        final_lines = lines + new_lines
        write_env(env_path, final_lines)
        return added, 0, 0

    return 0, 0, 0


# ═══════════════════════════════════════════════════════════
#  PREVIEW
# ═══════════════════════════════════════════════════════════
def preview_env(env_path, items, key_prefix="SLUG", limit=15):
    section("👀 PREVIEW")

    print(f"  📁 .env    : {env_path}")
    print(f"  📊 Item    : {len(items)}")
    print(f"  🔑 Prefix  : {key_prefix}_N")
    print()

    _, existing = parse_env(env_path)
    existing_count = sum(1 for k in existing.keys() if k.startswith(f"{key_prefix}_"))
    print(f"  📋 Existing : {existing_count} key dengan prefix '{key_prefix}_'")
    print()

    print("  Preview output:")
    cprint("  " + "-" * 60, C.DIM)
    for i, item in enumerate(items[:limit], 1):
        value = item["value"]
        print(f"  {key_prefix}_{i}={value}")

    if len(items) > limit:
        print(f"  ... dan {len(items) - limit} lagi")
    cprint("  " + "-" * 60, C.DIM)


# ═══════════════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════════════
MENU = """
╔══════════════════════════════════════════════════════════╗
║           ⚙️  ADD ENV — Edit .env dari JSON              ║
╠══════════════════════════════════════════════════════════╣
║  SOURCE (data/base/slugs/)                               ║
║    [1] 📋 List JSON files                                ║
║    [2] 🔄 Refresh list                                   ║
║                                                          ║
║  ACTION                                                  ║
║    [3] 👀 Preview (pilih file)                           ║
║    [4] 🔄 Replace .env (hapus lama, tulis baru)          ║
║    [5] ➕ Merge .env (tambah ke existing)                ║
║                                                          ║
║  CONFIG                                                  ║
║    [6] 🔑 Ganti prefix key (SLUG/GENRE/ANIME)            ║
║    [7] 📁 Ganti folder source                            ║
║    [8] 💾 Backup .env                                    ║
║    [9] 📄 Lihat .env sekarang                            ║
║                                                          ║
║    [0] Keluar                                            ║
╚══════════════════════════════════════════════════════════╝
"""


def ask_text(prompt, default=""):
    if default:
        val = input(f"  {prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"  {prompt}: ").strip()


def ask_yes_no(question, default_yes=True):
    suffix = "[Y/n]" if default_yes else "[y/N]"
    answer = input(f"  {question} {suffix} (enter): ").strip().lower()
    if not answer:
        return default_yes
    return answer in ("y", "ya", "yes", "1")


def interactive_menu():
    current_source = SLUGS_DIR
    current_env = DEFAULT_ENV
    current_prefix = "SLUG"

    while True:
        section("⚙️  ADD ENV — Edit .env dari JSON")

        files = find_json_files(current_source)

        print()
        print(f"  📁 Source   : {current_source}")
        print(f"  📁 .env     : {current_env}")
        print(f"  🔑 Prefix   : {current_prefix}_N")
        print(f"  📄 Files    : {len(files)}")

        if files:
            print()
            print(f"  Files ({len(files)}):")
            for i, f in enumerate(files[:5], 1):
                print(f"    [{i}] {f['rel']} ({f['count']} item)")
            if len(files) > 5:
                print(f"    ... dan {len(files) - 5} lagi")

        print(MENU)

        choice = input(f"  {C.CYAN}Pilih: {C.RESET}").strip()

        try:
            if choice == "0":
                cprint("\n  👋 Bye!", C.CYAN)
                break

            elif choice == "1":
                section("📋 JSON FILES")
                display_json_files(files)

            elif choice == "2":
                cprint("  🔄 Refresh...", C.DIM)
                files = find_json_files(current_source)

            elif choice in ("3", "4", "5"):
                if not files:
                    cprint("  ❌ Tidak ada file JSON", C.RED)
                    continue

                # Pilih file
                selected = select_json_file(files)

                if selected is None:
                    cprint("  ❌ Dibatalkan", C.YELLOW)
                    continue

                # Load items
                if isinstance(selected, list):
                    # Multiple files
                    items = load_multiple_jsons(selected)
                    cprint(f"  ✅ {len(items)} item dari {len(selected)} file", C.GREEN)
                else:
                    items = load_json(selected)
                    cprint(f"  ✅ {len(items)} item dari {selected.name}", C.GREEN)

                if not items:
                    cprint("  ⚠️  JSON kosong", C.YELLOW)
                    continue

                # Preview
                if choice == "3":
                    preview_env(current_env, items, current_prefix)

                elif choice == "4":
                    preview_env(current_env, items, current_prefix)
                    print()
                    if ask_yes_no(f"Replace .env? ({len(items)} item)", default_yes=True):
                        backup = backup_env(current_env)
                        if backup:
                            cprint(f"  💾 Backup: {backup}", C.DIM)

                        added, updated, removed = update_env(
                            current_env, items, current_prefix, mode="replace"
                        )
                        cprint(f"\n  ✅ Replace selesai", C.GREEN)
                        print(f"     Ditambah : {added}")
                        print(f"     Dihapus  : {removed}")

                elif choice == "5":
                    if ask_yes_no(f"Merge {len(items)} item ke .env?", default_yes=True):
                        backup = backup_env(current_env)
                        if backup:
                            cprint(f"  💾 Backup: {backup}", C.DIM)

                        added, updated, removed = update_env(
                            current_env, items, current_prefix, mode="merge"
                        )
                        cprint(f"\n  ✅ Merge selesai", C.GREEN)
                        print(f"     Ditambah : {added}")

            elif choice == "6":
                p = ask_text("Prefix (SLUG/GENRE/ANIME)", current_prefix)
                if p:
                    current_prefix = p.upper().strip()
                    cprint(f"  ✅ Prefix: {current_prefix}", C.GREEN)

            elif choice == "7":
                p = ask_text("Folder source", str(current_source))
                if p:
                    current_source = Path(p)
                    cprint(f"  ✅ Source: {current_source}", C.GREEN)

            elif choice == "8":
                b = backup_env(current_env)
                if b:
                    cprint(f"  ✅ Backup: {b}", C.GREEN)
                else:
                    cprint(f"  ⚠️  .env tidak ada", C.YELLOW)

            elif choice == "9":
                if current_env.exists():
                    print()
                    cprint(f"  📄 {current_env}:", C.BOLD)
                    cprint("  " + "-" * 60, C.DIM)
                    content = current_env.read_text(encoding="utf-8")
                    # Show only SLUG_N lines
                    for line in content.split("\n"):
                        if re.match(r"^(SLUG|GENRE|ANIME)_\d+", line) or line.startswith("#"):
                            print(line)
                    cprint("  " + "-" * 60, C.DIM)
                else:
                    cprint(f"  ⚠️  .env tidak ada", C.YELLOW)

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
        description="Edit .env dari JSON di data/base/slugs/",
    )
    ap.add_argument("--input", "-i", type=str, default=None,
                    help="Path JSON input (custom)")
    ap.add_argument("--env", "-e", type=str, default=str(DEFAULT_ENV),
                    help="Path .env")
    ap.add_argument("--key", "-k", type=str, default="SLUG",
                    help="Prefix key (SLUG/GENRE/ANIME)")
    ap.add_argument("--list", "-l", action="store_true",
                    help="List JSON files")
    ap.add_argument("--preview", "-p", action="store_true",
                    help="Preview saja")
    ap.add_argument("--select", type=int, default=None,
                    help="Pilih file index (1-based)")
    ap.add_argument("--merge", "-m", action="store_true",
                    help="Merge, bukan replace")
    ap.add_argument("--backup", "-b", action="store_true",
                    help="Backup .env dulu")
    ap.add_argument("--yes", "-y", action="store_true",
                    help="Skip konfirmasi")

    args = ap.parse_args()

    # List mode
    if args.list:
        section("📋 JSON FILES")
        files = find_json_files(SLUGS_DIR)
        display_json_files(files)
        return

    # Tentukan file input
    if args.input:
        selected = Path(args.input)
        if not selected.exists():
            cprint(f"❌ File tidak ada: {selected}", C.RED)
            sys.exit(1)
    elif args.select is not None:
        files = find_json_files(SLUGS_DIR)
        if not files:
            cprint("❌ Tidak ada file JSON di data/base/slugs/", C.RED)
            sys.exit(1)
        if 1 <= args.select <= len(files):
            selected = files[args.select - 1]["path"]
        else:
            cprint(f"❌ Index tidak valid (1-{len(files)})", C.RED)
            sys.exit(1)
    else:
        # Auto-pick dari slugs/
        files = find_json_files(SLUGS_DIR)
        if not files:
            cprint("❌ Tidak ada file JSON di data/base/slugs/", C.RED)
            sys.exit(1)
        if len(files) == 1:
            selected = files[0]["path"]
        else:
            # Menu pilih
            section("📁 PILIH FILE JSON")
            selected = select_json_file(files)
            if selected is None:
                cprint("❌ Dibatalkan", C.YELLOW)
                sys.exit(0)

    # Load items
    if isinstance(selected, list):
        items = load_multiple_jsons(selected)
    else:
        items = load_json(selected)

    if not items:
        cprint("❌ Tidak ada item", C.RED)
        sys.exit(1)

    # Preview
    preview_env(args.env, items, args.key.upper())

    if args.preview:
        return

    # Konfirmasi
    if not args.yes:
        mode = "MERGE" if args.merge else "REPLACE"
        if not ask_yes_no(f"{mode} .env?", default_yes=True):
            cprint("  ❌ Dibatalkan", C.YELLOW)
            return

    # Backup
    if args.backup:
        b = backup_env(args.env)
        if b:
            cprint(f"  💾 Backup: {b}", C.DIM)

    # Update
    mode = "merge" if args.merge else "replace"
    added, updated, removed = update_env(
        args.env, items, args.key.upper(), mode=mode
    )

    section("✅ SELESAI")
    print(f"  Ditambah : {added}")
    if removed:
        print(f"  Dihapus  : {removed}")
    print(f"  .env     : {args.env}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted\n")
        sys.exit(130)