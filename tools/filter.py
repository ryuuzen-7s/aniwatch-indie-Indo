"""
filter.py - Filter file sampah & backup.

Jalankan:
    python tools/filter.py                # dry-run (preview saja)
    python tools/filter.py --run          # eksekusi
    python tools/filter.py --run --yes    # tanpa konfirmasi
    python tools/filter.py --stats        # statistik file

Rules:
    _*.py          → bin/       (script temporary)
    *.txt (non-root) → bin/     (dokumen random)
    *.bak          → backup/    (backup)
    *.example      → backup/    (template)
    *.old          → bin/
    *.tmp          → bin/
"""
import sys
import shutil
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
BIN_DIR = ROOT / "bin"
BACKUP_DIR = ROOT / "backup"

# File yang DI-KEEP (jangan pernah dipindah)
KEEP_FILES = {
    "main.py",
    "config.py",
    "requirements.txt",
    "README.md",
    ".env",
    ".env.example",
    ".gitignore",
    "tools.bat",
}

# File yang DI-KEEP di root (boleh .txt)
KEEP_ROOT_EXT = {".md", ".txt", ".bat", ".env"}

# Folder yang di-skip (jangan disentuh)
SKIP_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "env",
    "node_modules", ".pytest_cache", ".ruff_cache",
    ".vscode", ".idea", "data", "bin", "backup",
    "logs", "output", "aniwatch_output", "debug_output",
    "env_backup", "scrape_output", "resolver_output",
    "api", "core", "db", "cache", "security",
    "control", "agent", "web", "docs", "test", "tools",
    "deploy", "scripts", "fixed",
}

# Rules: pattern → target folder
RULES = [
    # (nama mulai dengan, target)
    ("_", "bin"),          # _*.py, _*.txt (temporary)
    ("test_", "bin"),      # test_*.py yang di root (biasanya sementara)
]

# Extension → target
EXT_RULES = {
    # Backup
    ".bak": "backup",
    ".example": "backup",
    ".old": "backup",
    ".orig": "backup",
    ".save": "backup",
    ".swp": "bin",
    ".tmp": "bin",
    ".temp": "bin",
    ".log": "bin",
    ".lock": "bin",
}


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


def section(title, color=None):
    color = color or C.CYAN
    print()
    cprint("=" * 76, color)
    cprint("  " + title, C.BOLD + color)
    cprint("=" * 76, color)


# ═══════════════════════════════════════════════════════════
#  FILTER LOGIC
# ═══════════════════════════════════════════════════════════
def should_skip(path):
    """Cek apakah path di-skip."""
    # Skip folder tertentu
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    return False


def should_keep(path):
    """Cek apakah file di-keep (tidak dipindah)."""
    name = path.name

    # File yang di-keep by name
    if name in KEEP_FILES:
        return True

    # File di root dengan extension yang di-keep
    if path.parent == ROOT:
        ext = path.suffix.lower()
        if ext in KEEP_ROOT_EXT:
            # Kecuali yang match rules
            for prefix, _ in RULES:
                if name.startswith(prefix):
                    return False
            return True

    return False


def classify(path):
    """
    Tentukan file ini mau dikemanakan.
    Return: (target_dir, reason) atau (None, reason) kalau keep.
    """
    name = path.name
    ext = path.suffix.lower()
    is_root = path.parent == ROOT

    # 1. Cek keep list
    if should_keep(path):
        return None, "keep (whitelist)"

    # 2. Cek rules by name prefix
    for prefix, target in RULES:
        if name.startswith(prefix):
            # Skip tool files (tools/ folder sudah di-skip)
            # Skip __init__.py
            if name == "__init__.py":
                return None, "keep (__init__)"
            return target, f"prefix '{prefix}'"

    # 3. Cek extension rules
    if ext in EXT_RULES:
        return EXT_RULES[ext], f"extension '{ext}'"

    # 4. File .txt di luar root → bin/
    if ext == ".txt" and not is_root:
        return "bin", "txt non-root"

    # 5. File non-root yang mencurigakan
    # Kalau bukan salah satu extension penting
    VALID_EXTS = {
        ".py", ".js", ".css", ".html", ".json", ".md",
        ".bat", ".sh", ".yml", ".yaml", ".toml", ".ini",
        ".env", ".sql", ".txt", ".svg", ".png", ".jpg",
        ".ico", ".woff", ".woff2", ".ttf", ".eot",
    }

    if ext and ext not in VALID_EXTS and not is_root:
        return "bin", f"extension '{ext}' tidak valid"

    return None, "keep"


# ═══════════════════════════════════════════════════════════
#  SCAN & MOVE
# ═══════════════════════════════════════════════════════════
def scan_files():
    """Scan semua file, return dict: target → list of files."""
    targets = defaultdict(list)

    for f in ROOT.rglob("*"):
        if not f.is_file():
            continue

        try:
            rel = f.relative_to(ROOT)
        except ValueError:
            continue

        if should_skip(rel):
            continue

        target, reason = classify(f)
        if target:
            targets[target].append({
                "file": f,
                "rel": rel,
                "reason": reason,
                "size": f.stat().st_size,
            })

    return targets


def move_files(targets, dry_run=True, yes=False):
    """Pindahkan file."""
    BIN_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)

    total = sum(len(v) for v in targets.values())

    if total == 0:
        cprint("\n  ✅ Tidak ada file yang perlu dipindah", C.GREEN)
        return

    # Preview
    section(f"📋 PREVIEW ({total} file)", C.YELLOW)

    for target, files in sorted(targets.items()):
        dir_name = target + "/"
        total_size = sum(f["size"] for f in files)
        print()
        cprint(f"  📁 Ke {dir_name} ({len(files)} file, {total_size / 1024:.1f} KB)",
               C.BOLD + C.MAGENTA)

        for f in sorted(files, key=lambda x: x["rel"]):
            size_str = f"{f['size']:>8,} bytes"
            reason = f["reason"]
            print(f"     {str(f['rel']):<50} {size_str}  [{reason}]")

    # Dry run?
    if dry_run:
        print()
        cprint("  💡 Ini dry-run. Jalankan dengan --run untuk eksekusi.", C.YELLOW)
        return

    # Konfirmasi
    if not yes:
        print()
        confirm = input(f"  Pindahkan {total} file? (Y/n): ").strip().lower()
        if confirm and confirm not in ("y", "ya", "yes"):
            cprint("  ❌ Dibatalkan", C.YELLOW)
            return

    # Eksekusi
    section("🚚 MEMINDAHKAN FILE", C.GREEN)

    moved = 0
    failed = 0
    by_target = defaultdict(int)

    for target, files in targets.items():
        target_dir = BIN_DIR if target == "bin" else BACKUP_DIR
        target_dir.mkdir(exist_ok=True)

        for f in files:
            src = f["file"]
            dst = target_dir / src.name

            # Kalau nama sama sudah ada, tambah timestamp
            if dst.exists():
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                dst = target_dir / f"{src.stem}_{ts}{src.suffix}"

            try:
                shutil.move(str(src), str(dst))
                print(f"  ✅ {str(f['rel']):<50} → {target}/")
                moved += 1
                by_target[target] += 1
            except Exception as e:
                print(f"  ❌ {str(f['rel']):<50} GAGAL: {e}")
                failed += 1

    # Ringkasan
    section("📊 SELESAI", C.GREEN)
    print()
    print(f"  ✅ Berhasil dipindah : {moved}")
    if failed:
        print(f"  ❌ Gagal             : {failed}")
    print()
    print(f"  Detail:")
    for target, count in sorted(by_target.items()):
        print(f"    {target}/  : {count} file")
    print()
    cprint(f"  📁 bin/     : {BIN_DIR}", C.CYAN)
    cprint(f"  📁 backup/  : {BACKUP_DIR}", C.CYAN)


# ═══════════════════════════════════════════════════════════
#  SHOW STATISTICS
# ═══════════════════════════════════════════════════════════
def show_stats(targets):
    """Tampilkan statistik file."""
    section("📊 STATISTIK FILE")

    total = sum(len(v) for v in targets.values())
    total_size = sum(f["size"] for v in targets.values() for f in v)

    print(f"  📊 Total file     : {total}")
    print(f"  💾 Total size     : {total_size / 1024:.1f} KB")
    print()

    if not targets:
        cprint("  ✅ Tidak ada file yang perlu dipindah", C.GREEN)
        return

    print(f"  Breakdown per target:")
    for target, files in sorted(targets.items()):
        size = sum(f["size"] for f in files)
        bar = "█" * min(len(files), 40)
        print(f"    {target:<10} : {len(files):>3} file  {size / 1024:>8.1f} KB  {bar}")


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(
        description="Filter file sampah & backup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Rules:
  _*.py           → bin/       (script temporary)
  *.txt (non-root) → bin/      (dokumen random)
  *.bak           → backup/    (backup)
  *.example       → backup/    (template)
  *.old           → backup/
  *.tmp           → bin/
""",
    )
    ap.add_argument("--run", action="store_true",
                    help="Eksekusi pindah (default: dry-run)")
    ap.add_argument("--yes", "-y", action="store_true",
                    help="Skip konfirmasi")
    ap.add_argument("--stats", "-s", action="store_true",
                    help="Tampilkan statistik saja")

    args = ap.parse_args()

    # Header
    print()
    cprint("=" * 76, C.CYAN)
    cprint("  🧹 ANIWATCH FILTER — File Cleanup", C.BOLD + C.CYAN)
    cprint("=" * 76, C.CYAN)
    print()
    print(f"  📁 Root     : {ROOT}")
    print(f"  📁 Bin      : {BIN_DIR}")
    print(f"  📁 Backup   : {BACKUP_DIR}")
    print()

    # Scan
    cprint("  🔍 Scanning...", C.DIM)
    targets = scan_files()

    if args.stats:
        show_stats(targets)
        return

    # Preview / Move
    move_files(targets, dry_run=not args.run, yes=args.yes)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⏸️  Interrupted\n")
        sys.exit(130)