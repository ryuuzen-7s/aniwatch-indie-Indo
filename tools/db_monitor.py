"""
db_monitor.py - CLI Monitor + Manage DB AniWatch.

Jalankan:
    python db_monitor.py                 # menu interaktif
    python db_monitor.py --live          # live monitor (htop style)
    python db_monitor.py --once          # tampilkan stats sekali
    python db_monitor.py --watch 2       # refresh tiap 2 detik
"""
import sys
import os
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from sqlalchemy import (
    select, func, text, inspect, MetaData,
    Table, Column, Integer, String, Text, Boolean, Float, DateTime,
)
from pathlib import Path
import sys
# ═══════════════════════════════════════════════════════════
#  PATH FIX — supaya bisa import dari root project
# ═══════════════════════════════════════════════════════════
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# ═══════════════════════════════════════════════════════════

from db import get_session, engine, db_info
from db.models import Anime, Episode, DownloadLink, Report, User, ApiKey


# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
START_TIME = time.time()
MONITOR_NAME = "Aniwatch Monitoring Base"


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


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════
def format_size(bytes_size):
    """Format byte size ke KB/MB/GB/TB."""
    if bytes_size is None:
        return "0 B"
    size = float(bytes_size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def format_uptime(seconds):
    """Format detik jadi 'Xh Ym Zs'."""
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def get_uptime():
    return format_uptime(time.time() - START_TIME)


def get_db_size():
    """Size file DB."""
    db_path = Path(db_info()["path"])
    if db_path.exists():
        return format_size(db_path.stat().st_size)
    return "0 B"


# ═══════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════
def get_counts():
    """Ambil count semua tabel utama."""
    counts = {}
    try:
        with get_session() as s:
            counts["anime"] = s.scalar(select(func.count()).select_from(Anime)) or 0
            counts["episode"] = s.scalar(select(func.count()).select_from(Episode)) or 0
            counts["download"] = s.scalar(select(func.count()).select_from(DownloadLink)) or 0
            counts["report"] = s.scalar(select(func.count()).select_from(Report)) or 0
            counts["user"] = s.scalar(select(func.count()).select_from(User)) or 0
            counts["api_key"] = s.scalar(select(func.count()).select_from(ApiKey)) or 0
    except Exception as e:
        counts["error"] = str(e)
    return counts


def get_table_list():
    """Ambil daftar tabel dari DB."""
    try:
        insp = inspect(engine)
        return insp.get_table_names()
    except Exception:
        return []


def get_table_info(table_name):
    """Info detail tabel: rows, columns, size estimate."""
    try:
        insp = inspect(engine)

        # Cek tabel ada
        if table_name not in insp.get_table_names():
            return None

        # Columns
        columns = insp.get_columns(table_name)

        # Rows
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            rows = result.scalar()

        # Size estimate (SQLite only)
        size = 0
        try:
            with engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT SUM(pgsize) FROM dbstat WHERE name = :name"
                ), {"name": table_name})
                size = result.scalar() or 0
        except Exception:
            pass

        return {
            "name": table_name,
            "rows": rows,
            "columns": columns,
            "size": size,
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
#  DISPLAY: HEADER
# ═══════════════════════════════════════════════════════════
def print_header(live=False):
    """Print header monitoring."""
    counts = get_counts()
    db_size = get_db_size()
    uptime = get_uptime()

    # Clear kalau live mode
    if live:
        clear_screen()

    # Bar
    print("=" * 60)
    print(f"  {C.BOLD}{C.CYAN}{MONITOR_NAME}{C.RESET}")
    print("=" * 60)
    print(f"  uptime  : {C.GREEN}{uptime}{C.RESET}")
    print(f"  DB size : {C.GREEN}{db_size}{C.RESET}")
    print()
    print(f"  Anime     : {C.YELLOW}{counts.get('anime', 0)}{C.RESET}")
    print(f"  Episode   : {C.YELLOW}{counts.get('episode', 0)}{C.RESET}")
    print(f"  Download  : {C.YELLOW}{counts.get('download', 0)}{C.RESET}")
    print(f"  Report    : {C.YELLOW}{counts.get('report', 0)}{C.RESET}")
    print(f"  User      : {C.YELLOW}{counts.get('user', 0)}{C.RESET}")
    print(f"  Api Key   : {C.YELLOW}{counts.get('api_key', 0)}{C.RESET}")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════
#  DISPLAY: MENU
# ═══════════════════════════════════════════════════════════
def print_menu():
    print()
    print("  OPTION:")
    print("    1. Cek Query      - Lihat data dengan query custom")
    print("    2. Cek Tabel      - Lihat daftar tabel + info")
    print("    3. Hapus Query    - Hapus row dengan WHERE")
    print("    4. Hapus Tabel    - Hapus tabel (DROP)")
    print("    5. Tambah Tabel   - Buat tabel baru")
    print("    6. Tambah Query   - INSERT row custom")
    print("    7. Reset Query    - Reset / truncate tabel")
    print("    0. Keluar")
    print()


# ═══════════════════════════════════════════════════════════
#  INPUT HELPERS
# ═══════════════════════════════════════════════════════════
def ask_yes_no(question, default_yes=True):
    """Tanya Y/N, Enter = default."""
    suffix = "[Y/n]" if default_yes else "[y/N]"
    answer = input(f"  {question} {suffix} (enter): ").strip().lower()
    if not answer:
        return default_yes
    return answer in ("y", "ya", "yes", "1", "true")


def ask_text(prompt, default=""):
    """Input teks."""
    if default:
        val = input(f"  {prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"  {prompt}: ").strip()


# ═══════════════════════════════════════════════════════════
#  MENU 1: CEK QUERY
# ═══════════════════════════════════════════════════════════
def menu_cek_query():
    print()
    print("=" * 60)
    print("  🔍 CEK QUERY")
    print("=" * 60)
    print()

    print("  Contoh query:")
    print("    SELECT * FROM anime LIMIT 5")
    print("    SELECT id, title, slug FROM anime WHERE status = 'Ongoing'")
    print("    SELECT COUNT(*) FROM episode")
    print()

    query = input("  Query: ").strip()
    if not query:
        print("  ❌ Query kosong")
        return

    # Cek read-only (hanya SELECT)
    query_lower = query.lower().strip()
    if not query_lower.startswith("select"):
        print("  ⚠️  Hanya SELECT yang diizinkan di sini")
        print("     Untuk modifikasi, pakai menu lain")
        return

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            keys = result.keys()

        if not rows:
            print("  ℹ️  (tidak ada hasil)")
            return

        print()
        print(f"  📊 Hasil: {len(rows)} row(s)")
        print()

        # Header
        col_widths = []
        for k in keys:
            max_w = max(len(str(k)), 20)
            for r in rows[:10]:  # max 10 baris untuk lebar
                val_len = len(str(r._mapping[k])[:30])
                max_w = max(max_w, val_len)
            col_widths.append(min(max_w, 30))

        # Print header
        header = "  "
        for i, k in enumerate(keys):
            header += str(k)[:col_widths[i]].ljust(col_widths[i] + 2)
        print(C.BOLD + header + C.RESET)
        print("  " + "-" * (sum(col_widths) + len(col_widths) * 2))

        # Print rows (max 50)
        for r in rows[:50]:
            line = "  "
            for i, k in enumerate(keys):
                val = str(r._mapping[k])[:col_widths[i]]
                line += val.ljust(col_widths[i] + 2)
            print(line)

        if len(rows) > 50:
            print(f"  ... dan {len(rows) - 50} baris lagi")

    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════
#  MENU 2: CEK TABEL
# ═══════════════════════════════════════════════════════════
def menu_cek_tabel():
    print()
    print("=" * 60)
    print("  📋 CEK TABEL")
    print("=" * 60)
    print()

    tables = get_table_list()
    if not tables:
        print("  (tidak ada tabel)")
        return

    print(f"  Total: {len(tables)} tabel")
    print()

    print(f"  {'NAMA':<25} {'ROWS':>10} {'COLS':>6} {'SIZE':>12}")
    print("  " + "-" * 60)

    for tname in tables:
        info = get_table_info(tname)
        if info and "error" not in info:
            rows = info["rows"]
            cols = len(info["columns"])
            size = format_size(info["size"])
            print(f"  {tname:<25} {rows:>10} {cols:>6} {size:>12}")
        else:
            print(f"  {tname:<25} {'?':>10} {'?':>6} {'?':>12}")

    # Detail
    print()
    detail = ask_text("Lihat detail tabel? (nama/kosong)", "")
    if detail:
        info = get_table_info(detail)
        if not info:
            print(f"  ❌ Tabel '{detail}' tidak ditemukan")
            return
        if "error" in info:
            print(f"  ❌ Error: {info['error']}")
            return

        print()
        print(f"  📋 Tabel: {C.BOLD}{detail}{C.RESET}")
        print(f"  Rows   : {info['rows']}")
        print(f"  Size   : {format_size(info['size'])}")
        print()
        print("  Kolom:")
        print(f"  {'NAMA':<20} {'TIPE':<20} {'NULL':<6} {'PK'}")
        print("  " + "-" * 60)

        pk_cols = [c["name"] for c in info["columns"]]
        for col in info["columns"]:
            name = col["name"]
            ctype = str(col["type"])
            nullable = "YES" if col.get("nullable", True) else "NO"
            pk = "🔑" if col.get("primary_key") else ""
            print(f"  {name:<20} {ctype:<20} {nullable:<6} {pk}")


# ═══════════════════════════════════════════════════════════
#  MENU 3: HAPUS QUERY
# ═══════════════════════════════════════════════════════════
def menu_hapus_query():
    print()
    print("=" * 60)
    print("  🗑️  HAPUS QUERY")
    print("=" * 60)
    print()

    print("  Format: DELETE FROM table WHERE condition")
    print("  Contoh: DELETE FROM anime WHERE slug = 'test-anime'")
    print()

    query = input("  Query: ").strip()
    if not query:
        print("  ❌ Query kosong")
        return

    query_lower = query.lower().strip()
    if not query_lower.startswith("delete"):
        print("  ⚠️  Hanya DELETE yang diizinkan")
        return

    if " where " not in query_lower:
        print("  ⚠️  WAJIB pakai WHERE untuk keamanan")
        print("     Untuk hapus semua, pakai menu 'Reset Query'")
        return

    print()
    print(f"  Query: {C.YELLOW}{query}{C.RESET}")
    print()

    if not ask_yes_no("Jalankan DELETE?", default_yes=False):
        print("  ❌ Dibatalkan")
        return

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            conn.commit()
            rows_affected = result.rowcount
        print(f"  ✅ {rows_affected} row dihapus")
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════
#  MENU 4: HAPUS TABEL
# ═══════════════════════════════════════════════════════════
def menu_hapus_tabel():
    print()
    print("=" * 60)
    print("  🗑️  HAPUS TABEL (DROP)")
    print("=" * 60)
    print()

    tables = get_table_list()
    if not tables:
        print("  (tidak ada tabel)")
        return

    print(f"  Tabel tersedia ({len(tables)}):")
    for t in tables:
        print(f"    - {t}")
    print()

    tname = input("  Nama tabel yang mau dihapus: ").strip()
    if not tname:
        print("  ❌ Dibatalkan")
        return

    if tname not in tables:
        print(f"  ❌ Tabel '{tname}' tidak ada")
        return

    print()
    print(f"  {C.RED}⚠️  DROP TABLE {tname} — DATA AKAN HILANG PERMANEN!{C.RESET}")
    print()

    if not ask_yes_no(f"Hapus tabel '{tname}'?", default_yes=False):
        print("  ❌ Dibatalkan")
        return

    # Konfirmasi 2: ketik nama tabel
    confirm = input(f"  Ketik '{tname}' untuk konfirmasi: ").strip()
    if confirm != tname:
        print("  ❌ Dibatalkan")
        return

    try:
        with engine.connect() as conn:
            conn.execute(text(f"DROP TABLE {tname}"))
            conn.commit()
        print(f"  ✅ Tabel '{tname}' dihapus")
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════
#  MENU 5: TAMBAH TABEL
# ═══════════════════════════════════════════════════════════
def menu_tambah_tabel():
    print()
    print("=" * 60)
    print("  ➕ TAMBAH TABEL")
    print("=" * 60)
    print()

    print("  Format: CREATE TABLE nama (kolom1 TIPE, kolom2 TIPE, ...)")
    print("  Tipe: INTEGER, TEXT, REAL, BLOB, BOOLEAN, DATETIME")
    print()
    print("  Contoh:")
    print("    CREATE TABLE tags (id INTEGER PRIMARY KEY, name TEXT, created_at DATETIME)")
    print()

    query = input("  Query: ").strip()
    if not query:
        print("  ❌ Query kosong")
        return

    query_lower = query.lower().strip()
    if not query_lower.startswith("create"):
        print("  ⚠️  Hanya CREATE yang diizinkan")
        return

    print()
    print(f"  Query: {C.YELLOW}{query}{C.RESET}")
    print()

    if not ask_yes_no("Jalankan CREATE?", default_yes=True):
        print("  ❌ Dibatalkan")
        return

    try:
        with engine.connect() as conn:
            conn.execute(text(query))
            conn.commit()
        print("  ✅ Tabel berhasil dibuat")
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════
#  MENU 6: TAMBAH QUERY
# ═══════════════════════════════════════════════════════════
def menu_tambah_query():
    print()
    print("=" * 60)
    print("  ➕ TAMBAH QUERY (INSERT)")
    print("=" * 60)
    print()

    print("  Format: INSERT INTO table (kolom1, kolom2) VALUES (val1, val2)")
    print()
    print("  Contoh:")
    print("    INSERT INTO anime (source, slug, title) VALUES ('otakudesu', 'test', 'Test Anime')")
    print()

    query = input("  Query: ").strip()
    if not query:
        print("  ❌ Query kosong")
        return

    query_lower = query.lower().strip()
    if not query_lower.startswith("insert"):
        print("  ⚠️  Hanya INSERT yang diizinkan")
        return

    print()
    print(f"  Query: {C.YELLOW}{query}{C.RESET}")
    print()

    if not ask_yes_no("Jalankan INSERT?", default_yes=True):
        print("  ❌ Dibatalkan")
        return

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            conn.commit()
        print("  ✅ Row berhasil ditambahkan")
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════
#  MENU 7: RESET QUERY
# ═══════════════════════════════════════════════════════════
def menu_reset_query():
    print()
    print("=" * 60)
    print("  🔄 RESET QUERY (TRUNCATE)")
    print("=" * 60)
    print()

    tables = get_table_list()
    if not tables:
        print("  (tidak ada tabel)")
        return

    print(f"  Tabel tersedia ({len(tables)}):")
    for t in tables:
        info = get_table_info(t)
        rows = info["rows"] if info and "error" not in info else "?"
        print(f"    - {t:<25} ({rows} rows)")
    print()

    tname = input("  Nama tabel yang mau di-reset: ").strip()
    if not tname:
        print("  ❌ Dibatalkan")
        return

    if tname not in tables:
        print(f"  ❌ Tabel '{tname}' tidak ada")
        return

    print()
    print(f"  {C.RED}⚠️  RESET {tname} — SEMUA ROW AKAN DIHAPUS!{C.RESET}")
    print()

    if not ask_yes_no(f"Reset tabel '{tname}'?", default_yes=False):
        print("  ❌ Dibatalkan")
        return

    # Konfirmasi 2
    confirm = input(f"  Ketik 'RESET' untuk konfirmasi: ").strip()
    if confirm != "RESET":
        print("  ❌ Dibatalkan")
        return

    try:
        with engine.connect() as conn:
            conn.execute(text(f"DELETE FROM {tname}"))
            conn.commit()
        print(f"  ✅ Tabel '{tname}' di-reset")
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════════════
def interactive_menu():
    while True:
        clear_screen()
        print_header()
        print_menu()

        choice = input(f"  {C.CYAN}Pilih [0]: {C.RESET}").strip() or "0"

        try:
            if choice == "0":
                clear_screen()
                print(f"  {C.CYAN}👋 Bye!{C.RESET}")
                break
            elif choice == "1":
                menu_cek_query()
            elif choice == "2":
                menu_cek_tabel()
            elif choice == "3":
                menu_hapus_query()
            elif choice == "4":
                menu_hapus_tabel()
            elif choice == "5":
                menu_tambah_tabel()
            elif choice == "6":
                menu_tambah_query()
            elif choice == "7":
                menu_reset_query()
            else:
                print(f"  {C.YELLOW}❓ Pilihan tidak valid{C.RESET}")
        except KeyboardInterrupt:
            print(f"\n  {C.YELLOW}⏸️  Dibatalkan{C.RESET}")
        except Exception as e:
            print(f"  {C.RED}❌ Error: {type(e).__name__}: {e}{C.RESET}")

        if choice != "0":
            print()
            input(f"  {C.DIM}[Enter untuk lanjut]{C.RESET}")


# ═══════════════════════════════════════════════════════════
#  LIVE MONITOR
# ═══════════════════════════════════════════════════════════
def live_monitor(interval=2):
    """Live monitor (htop style) — refresh tiap X detik."""
    try:
        while True:
            print_header(live=True)
            print()
            print(f"  {C.DIM}Live mode - refresh tiap {interval}s - Ctrl+C untuk stop{C.RESET}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n  {C.CYAN}👋 Stopped{C.RESET}")


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="AniWatch DB Monitor")
    ap.add_argument("--live", action="store_true", help="Live monitor")
    ap.add_argument("--once", action="store_true", help="Tampilkan stats sekali")
    ap.add_argument("--watch", type=int, metavar="N", default=2, help="Refresh interval (detik)")
    args = ap.parse_args()

    if args.live:
        live_monitor(args.watch)
    elif args.once:
        print_header()
    else:
        interactive_menu()


if __name__ == "__main__":
    main()