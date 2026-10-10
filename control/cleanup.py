"""
control/cleanup.py — Bersihkan data tidak valid / duplikat.

Jalankan:
    python -m control.cleanup --test      # hapus test data
    python -m control.cleanup --orphan    # hapus episode tanpa anime
    python -m control.cleanup --dead      # hapus download mati
    python -m control.cleanup --stale     # hapus anime >30 hari tidak update
    python -m control.cleanup --all       # semua di atas
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from sqlalchemy import select, delete, func
from db import get_session
from db.models import Anime, Episode, DownloadLink


def clean_test():
    with get_session() as s:
        count = 0
        for slug in ["test-anime", "test-anime-updated"]:
            a = s.execute(select(Anime).where(Anime.slug == slug)).scalar_one_or_none()
            if a:
                s.delete(a)
                count += 1
    print(f"  🗑️  Deleted {count} test anime")


def clean_orphan():
    """Hapus episode/link yang yatim (anime_id/episode_id tidak ada)."""
    with get_session() as s:
        # Episodes without anime
        ep_orphan = s.execute(
            select(func.count()).select_from(Episode)
            .outerjoin(Anime, Episode.anime_id == Anime.id)
            .where(Anime.id.is_(None))
        ).scalar() or 0

        # Download links without episode
        dl_orphan = s.execute(
            select(func.count()).select_from(DownloadLink)
            .outerjoin(Episode, DownloadLink.episode_id == Episode.id)
            .where(Episode.id.is_(None))
        ).scalar() or 0

        print(f"  📊 Episodes orphan: {ep_orphan}")
        print(f"  📊 Downloads orphan: {dl_orphan}")

        # Delete orphans
        if ep_orphan:
            s.execute(
                delete(Episode).where(
                    Episode.anime_id.notin_(select(Anime.id))
                )
            )
        if dl_orphan:
            s.execute(
                delete(DownloadLink).where(
                    DownloadLink.episode_id.notin_(select(Episode.id))
                )
            )

        print(f"  🗑️  Cleaned orphan records")


def clean_dead_links():
    """Hapus download link yang is_alive=False."""
    with get_session() as s:
        count = s.scalar(
            select(func.count()).select_from(DownloadLink)
            .where(DownloadLink.is_alive.is_(False))
        ) or 0
        s.execute(delete(DownloadLink).where(DownloadLink.is_alive.is_(False)))
    print(f"  🗑️  Deleted {count} dead download links")


def clean_stale(days=30):
    """Hapus anime yang tidak di-update > N hari."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with get_session() as s:
        count = s.scalar(
            select(func.count()).select_from(Anime)
            .where(Anime.updated_at < cutoff)
        ) or 0
        s.execute(delete(Anime).where(Anime.updated_at < cutoff))
    print(f"  🗑️  Deleted {count} anime (stale >{days}d)")


def main():
    args = sys.argv[1:]

    print("=" * 62)
    print("  🧹 CLEANUP")
    print("=" * 62)

    if not args or "--all" in args:
        clean_test()
        clean_orphan()
        clean_dead_links()
    else:
        if "--test" in args:
            clean_test()
        if "--orphan" in args:
            clean_orphan()
        if "--dead" in args:
            clean_dead_links()
        if "--stale" in args:
            clean_stale()

    print()
    print("  ✅ Cleanup selesai")


if __name__ == "__main__":
    main()