"""
cleaner.py - Bersihkan folder bin/ dan backup/.

Jalankan:
    python tools/cleaner.py                 # kosongkan bin/
    python tools/cleaner.py --backup        # kosongkan backup/ juga
    python tools/cleaner.py --dry-run       # preview saja
    python tools/cleaner.py --yes           # tanpa konfirmasi
"""
import sys
import shutil
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
BIN_DIR = ROOT / "bin"
BACKUP_DIR = ROOT / "backup"


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


def format_size(bytes_size):
    """Format byte size ke KB/MB/GB."""
    if bytes_size is None or bytes_size == 0:
        return "0 B"
    size = float(bytes_size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


# ═══════════════════════════════════════════════════════════
#  SCAN
# ═══════════════════════════════════════════════════════════
def scan_dir(target_dir):
    """Scan folder, return list of files + total size."""
    if not target_dir.exists():
        return [], 0

    files = []
    total_size = 0

    for f in target_dir.rglob("*"):
        if f.is_file():
            try:
                size = f.stat().st_size
                files.append({
                    "file": f,
                    "rel": f.relative_to(target_dir),
                    "size": size,
                })
                total_size += size
            except Exception:
                pass

    return files, total_size


# ═══════════════════════════════════════════════════════════
#  CLEAN
# ═══════════════════════════════════════════════════════════
def clean_dir(target_dir, dry_run=False, yes=False):
    """Kosongkan folder."""
    files, total_size = scan_dir(target_dir)

    dir_name = target_dir.name
    section_header = f"CLEAN /{dir_name}/"

    print()
    cprint("=" * 60, C.CYAN)
    cprint(f"  {section_header}", C.BOLD + C.CYAN)
    cprint("=" * 60, C.CYAN)
    print()

    if not files:
        cprint("  (folder kosong)", C.DIM)
        print()
        cprint(f"  ✅ N/A B berhasil dikosongkan", C.GREEN)
        return 0, 0

    # Preview
    print(f"  📊 Jumlah file  : {len(files)}")
    print(f"  💾 Total ukuran : {format_size(total_size)}")
    print()

    # List file (max 20)
    limit = 20
    for f in files[:limit]:
        size_str = format_size(f["size"]).rjust(10)
        rel_str = str(f["rel"])[:45]
        print(f"     {rel_str:<45} {size_str}")

    if len(files) > limit:
        cprint(f"     ... dan {len(files) - limit} file lagi", C.DIM)

    print()

    # Dry run?
    if dry_run:
        cprint("  💡 Dry-run — tidak ada file dihapus", C.YELLOW)
        return 0, 0

    # Konfirmasi
    if not yes:
        try:
            confirm = input(f"  Hapus semua {len(files)} file? (Y/n): ").strip().lower()
            if confirm and confirm not in ("y", "ya", "yes"):
                cprint("  ❌ Dibatalkan", C.YELLOW)
                return 0, 0
        except KeyboardInterrupt:
            print()
            cprint("  ❌ Dibatalkan", C.YELLOW)
            return 0, 0

    # Hapus
    deleted = 0
    failed = 0

    for f in files:
        try:
            f["file"].unlink()
            deleted += 1
        except Exception as e:
            print(f"  ❌ {f['rel']}: {e}")
            failed += 1

    # Hapus subfolder kosong
    for d in sorted(target_dir.rglob("*"), reverse=True):
        if d.is_dir() and d != target_dir:
            try:
                if not any(d.iterdir()):
                    d.rmdir()
            except Exception:
                pass

    # Hasil
    print()
    if failed == 0:
        cprint(f"  ✅ {format_size(total_size)} B berhasil dikosongkan", C.GREEN)
    else:
        cprint(f"  ⚠️  {deleted} file dihapus, {failed} gagal", C.YELLOW)

    return deleted, total_size


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(
        description="Bersihkan folder bin/ dan backup/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python tools/cleaner.py                # kosongkan bin/ (konfirmasi)
  python tools/cleaner.py --dry-run      # preview saja
  python tools/cleaner.py --yes          # tanpa konfirmasi
  python tools/cleaner.py --backup       # kosongkan backup/ juga
""",
    )
    ap.add_argument("--backup", action="store_true",
                    help="Kosongkan backup/ juga")
    ap.add_argument("--dry-run", "-n", action="store_true",
                    help="Preview saja")
    ap.add_argument("--yes", "-y", action="store_true",
                    help="Skip konfirmasi")

    args = ap.parse_args()

    # ═══ HEADER ═══
    print()
    cprint("=" * 60, C.CYAN)
    cprint("  CLEANER — Bersihkan Folder", C.BOLD + C.CYAN)
    cprint("=" * 60, C.CYAN)
    print()
    print(f"  📁 Root     : {ROOT}")
    print(f"  📁 Bin      : {BIN_DIR}")
    print(f"  📁 Backup   : {BACKUP_DIR}")

    # ═══ MEMULAI SCAN ═══
    print()
    cprint("=" * 60, C.YELLOW)
    cprint("  MEMULAI SCAN", C.BOLD + C.YELLOW)
    cprint("=" * 60, C.YELLOW)
    print()

    # Scan bin
    bin_files, bin_size = scan_dir(BIN_DIR)
    backup_files, backup_size = scan_dir(BACKUP_DIR)

    print(f"  📂 bin/       : {len(bin_files)} file, {format_size(bin_size)}")
    print(f"  📂 backup/    : {len(backup_files)} file, {format_size(backup_size)}")
    print()
    print(f"  📊 Jumlah File   : {len(bin_files) + (len(backup_files) if args.backup else 0)}")
    total = bin_size + (backup_size if args.backup else 0)
    print(f"  💾 Total Ukuran  : {format_size(total)}")

    # ═══ CLEAN BIN ═══
    print()
    cprint("=" * 60, C.CYAN)
    cprint(f"  CLEAN /bin/", C.BOLD + C.CYAN)
    cprint("=" * 60, C.CYAN)

    deleted, size = clean_dir(BIN_DIR, dry_run=args.dry_run, yes=args.yes)

    # ═══ CLEAN BACKUP (opsional) ═══
    if args.backup:
        print()
        cprint("=" * 60, C.CYAN)
        cprint(f"  CLEAN /backup/", C.BOLD + C.CYAN)
        cprint("=" * 60, C.CYAN)

        deleted_b, size_b = clean_dir(BACKUP_DIR, dry_run=args.dry_run, yes=args.yes)
        deleted += deleted_b
        size += size_b

    # ═══ FINAL SUMMARY ═══
    print()
    cprint("=" * 60, C.GREEN)
    cprint("  SELESAI", C.BOLD + C.GREEN)
    cprint("=" * 60, C.GREEN)
    print()

    if args.dry_run:
        cprint("  💡 Mode dry-run — tidak ada file dihapus", C.YELLOW)
    else:
        cprint(f"  ✅ {format_size(size)} B berhasil dikosongkan", C.GREEN)
        print(f"     {deleted} file dihapus")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⏸️  Interrupted\n")
        sys.exit(130)