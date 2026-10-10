"""
control/db_control.py — CLI interaktif kontrol database AniWatch.

Jalankan:
    python -m control.db_control
    atau
    python control/db_control.py
"""
import sys
from pathlib import Path

# Path fix
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from sqlalchemy import select, func, text
from db import get_session, db_info, init_db, reset_db
from db.models import Anime, Episode, DownloadLink, Report


# ═══════════════════════════════════════════════════════════
#  ANSI COLORS
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


def cprint(text, color="", end="\n"):
    print(f"{color}{text}{C.RESET}", end=end)


# ═══════════════════════════════════════════════════════════
#  MENU ACTIONS
# ═══════════════════════════════════════════════════════════
def show_dbinfo():
    info = db_info()
    print()
    cprint("=" * 62, C.CYAN)
    cprint("  📊 DATABASE INFO", C.BOLD + C.CYAN)
    cprint("=" * 62, C.CYAN)
    print(f"  Path    : {info['path']}")
    print(f"  Size    : {info['size_kb']} KB")
    print(f"  Tables  : {', '.join(info['tables'])}")
    print(f"  WAL mode: {info['wal_mode']}")


def show_counts():
    print()
    cprint("=" * 62, C.CYAN)
    cprint("  📈 ROW COUNT", C.BOLD + C.CYAN)
    cprint("=" * 62, C.CYAN)

    with get_session() as s:
        for model, name, icon in [
            (Anime, "Anime", "🎬"),
            (Episode, "Episode", "📺"),
            (DownloadLink, "Download", "⬇️ "),
            (Report, "Report", "📮"),
        ]:
            n = s.scalar(select(func.count()).select_from(model)) or 0
            bar = "█" * min(n, 30)
            print(f"  {icon} {name:<10}: {n:>5}  {C.GREEN}{bar}{C.RESET}")


def list_anime():
    print()
    cprint("=" * 62, C.CYAN)
    cprint("  📚 ANIME LIST", C.BOLD + C.CYAN)
    cprint("=" * 62, C.CYAN)

    with get_session() as s:
        animes = list(s.execute(select(Anime).order_by(Anime.id)).scalars())
        if not animes:
            cprint("  (kosong — belum ada anime di DB)", C.YELLOW)
            return

        for a in animes:
            # Hitung episode & download
            ep_count = s.scalar(
                select(func.count()).select_from(Episode).where(Episode.anime_id == a.id)
            ) or 0
            dl_count = s.scalar(
                select(func.count()).select_from(DownloadLink)
                .join(Episode).where(Episode.anime_id == a.id)
            ) or 0

            print()
            cprint(f"  🎬 [{a.id}] {a.title}", C.BOLD + C.BLUE)
            print(f"     Slug     : {a.slug}")
            print(f"     Source   : {a.source}")
            print(f"     Studio   : {a.studio or '-'}")
            print(f"     Status   : {a.status or '-'}")
            print(f"     Genre    : {', '.join(a.genres or []) or '-'}")
            print(f"     Episode  : {ep_count} di DB  (total {a.total_episode or '?'})")
            print(f"     Download : {dl_count} link")
            print(f"     Scraped  : {a.scraped_at}")


def list_episodes(slug=None):
    print()
    cprint("=" * 62, C.CYAN)
    cprint(f"  📺 EPISODE LIST" + (f" — {slug}" if slug else ""), C.BOLD + C.CYAN)
    cprint("=" * 62, C.CYAN)

    with get_session() as s:
        if slug:
            anime = s.execute(select(Anime).where(Anime.slug == slug)).scalar_one_or_none()
            if not anime:
                cprint(f"  ❌ Anime '{slug}' tidak ada", C.RED)
                return
            animes = [anime]
        else:
            animes = list(s.execute(select(Anime)).scalars())

        if not animes:
            cprint("  (kosong)", C.YELLOW)
            return

        for a in animes:
            eps = list(s.execute(
                select(Episode).where(Episode.anime_id == a.id)
                .order_by(Episode.episode_number.asc().nulls_last())
            ).scalars())

            if not eps:
                continue

            print()
            cprint(f"  🎬 {a.title}", C.BOLD + C.BLUE)
            for ep in eps:
                dl_count = s.scalar(
                    select(func.count()).select_from(DownloadLink)
                    .where(DownloadLink.episode_id == ep.id)
                ) or 0
                print(f"     • Ep#{str(ep.episode_number or '?'):>3}  "
                      f"{ep.title[:50]:<50}  "
                      f"{C.GREEN}{dl_count:>3} dl{C.RESET}  "
                      f"{C.DIM}{ep.stream_host or '-'}{C.RESET}")


def list_downloads(slug=None, only_alive=False):
    print()
    cprint("=" * 62, C.CYAN)
    cprint("  ⬇️  DOWNLOAD LINKS", C.BOLD + C.CYAN)
    cprint("=" * 62, C.CYAN)

    with get_session() as s:
        stmt = select(DownloadLink)
        if slug:
            stmt = stmt.join(Episode).join(Anime).where(Anime.slug == slug)
        if only_alive:
            stmt = stmt.where(DownloadLink.is_alive.is_(True))

        dls = list(s.execute(stmt.limit(100)).scalars())
        if not dls:
            cprint("  (kosong)", C.YELLOW)
            return

        for d in dls:
            icon = f"{C.GREEN}✅{C.RESET}" if d.is_alive else f"{C.RED}❌{C.RESET}"
            print(f"  {icon} [{d.quality:<12}] {d.host:<12} → "
                  f"{d.final_host or '?'}  ({d.status or '-'})")


def list_reports(only_unresolved=False):
    print()
    cprint("=" * 62, C.CYAN)
    cprint("  📮 REPORTS", C.BOLD + C.CYAN)
    cprint("=" * 62, C.CYAN)

    with get_session() as s:
        stmt = select(Report).order_by(Report.created_at.desc()).limit(50)
        if only_unresolved:
            stmt = stmt.where(Report.resolved.is_(False))

        reports = list(s.execute(stmt).scalars())
        if not reports:
            cprint("  (kosong)", C.YELLOW)
            return

        for r in reports:
            icon = "✅" if r.resolved else "🔴"
            print(f"  {icon} [{r.type:<10}] {r.slug:<30} {r.reason[:40]}")


# ═══════════════════════════════════════════════════════════
#  DELETE ACTIONS
# ═══════════════════════════════════════════════════════════
def delete_anime(slug):
    with get_session() as s:
        anime = s.execute(select(Anime).where(Anime.slug == slug)).scalar_one_or_none()
        if not anime:
            cprint(f"  ❌ '{slug}' tidak ada", C.RED)
            return False
        s.delete(anime)
        cprint(f"  🗑️  Deleted anime: {slug}", C.YELLOW)
        return True


def delete_test_data():
    with get_session() as s:
        deleted = []
        for slug in ["test-anime", "test-anime-updated"]:
            a = s.execute(select(Anime).where(Anime.slug == slug)).scalar_one_or_none()
            if a:
                s.delete(a)
                deleted.append(slug)

        if deleted:
            cprint(f"  🗑️  Deleted: {', '.join(deleted)}", C.YELLOW)
        else:
            cprint("  ℹ️  Tidak ada test data", C.DIM)


def delete_all_anime():
    confirm = input(f"{C.RED}⚠️  Hapus SEMUA anime? (ketik 'YA'): {C.RESET}").strip()
    if confirm != "YA":
        cprint("  ❌ Dibatalkan", C.YELLOW)
        return

    with get_session() as s:
        count = s.scalar(select(func.count()).select_from(Anime)) or 0
        s.execute(text("DELETE FROM anime"))

    cprint(f"  🗑️  Deleted {count} anime", C.YELLOW)


def delete_all_reports():
    with get_session() as s:
        count = s.scalar(select(func.count()).select_from(Report)) or 0
        s.execute(text("DELETE FROM report"))
    cprint(f"  🗑️  Deleted {count} reports", C.YELLOW)


# ═══════════════════════════════════════════════════════════
#  MAINTENANCE
# ═══════════════════════════════════════════════════════════
def vacuum_db():
    with get_session() as s:
        s.execute(text("VACUUM"))
    cprint("  ✅ VACUUM selesai (DB compacted)", C.GREEN)


def reset_database():
    confirm = input(f"{C.RED}⚠️  RESET seluruh DB? (ketik 'RESET'): {C.RESET}").strip()
    if confirm != "RESET":
        cprint("  ❌ Dibatalkan", C.YELLOW)
        return
    reset_db()
    cprint("  ✅ Database direset", C.GREEN)


def init_database():
    init_db()
    cprint("  ✅ Database initialized", C.GREEN)


# ═══════════════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════════════
MENU = """
╔══════════════════════════════════════════════════════════════╗
║              🎛️  ANIWATCH DB CONTROL                          ║
╠══════════════════════════════════════════════════════════════╣
║  INSPECT                                                     ║
║    [1] 📊 Info DB                                            ║
║    [2] 📈 Row count                                          ║
║    [3] 📚 List anime                                         ║
║    [4] 📺 List episode                                       ║
║    [5] ⬇️  List download                                     ║
║    [6] 📮 List report                                        ║
║                                                              ║
║  DELETE                                                      ║
║    [7]  🗑️  Hapus anime by slug                             ║
║    [8]  🗑️  Hapus test data                                 ║
║    [9]  🗑️  Hapus SEMUA anime                               ║
║    [10] 🗑️  Hapus SEMUA report                              ║
║                                                              ║
║  MAINTENANCE                                                 ║
║    [11] ⚡ VACUUM (compact DB)                              ║
║    [12] 🔄 Init DB                                          ║
║    [13] ⚠️  RESET DB (hapus semua tabel)                    ║
║                                                              ║
║    [0]  🚪 Exit                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def main():
    while True:
        print(MENU)
        choice = input(f"{C.CYAN}  Pilih menu: {C.RESET}").strip()

        try:
            if choice == "0":
                cprint("\n  👋 Bye!", C.CYAN)
                break
            elif choice == "1":
                show_dbinfo()
            elif choice == "2":
                show_counts()
            elif choice == "3":
                list_anime()
            elif choice == "4":
                slug = input("  Slug (kosong = semua): ").strip() or None
                list_episodes(slug)
            elif choice == "5":
                slug = input("  Slug (kosong = semua): ").strip() or None
                alive = input("  Only alive? (y/n): ").strip().lower() == "y"
                list_downloads(slug, alive)
            elif choice == "6":
                unresolved = input("  Only unresolved? (y/n): ").strip().lower() == "y"
                list_reports(unresolved)
            elif choice == "7":
                slug = input("  Slug anime: ").strip()
                if slug:
                    delete_anime(slug)
            elif choice == "8":
                delete_test_data()
            elif choice == "9":
                delete_all_anime()
            elif choice == "10":
                delete_all_reports()
            elif choice == "11":
                vacuum_db()
            elif choice == "12":
                init_database()
            elif choice == "13":
                reset_database()
            else:
                cprint("  ❓ Pilihan tidak valid", C.YELLOW)
        except KeyboardInterrupt:
            cprint("\n  ⏸️  Dibatalkan", C.YELLOW)
            continue
        except Exception as e:
            cprint(f"  ❌ Error: {type(e).__name__}: {e}", C.RED)

        # Pause sebelum kembali ke menu
        print()
        try:
            input(f"{C.DIM}  [Enter untuk lanjut]{C.RESET}")
        except KeyboardInterrupt:
            pass
        print("\033[2J\033[H", end="")  # clear screen


if __name__ == "__main__":
    main()