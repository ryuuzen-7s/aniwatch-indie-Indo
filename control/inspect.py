"""
control/inspect.py — Inspeksi detail DB.
Jalankan: python -m control.inspect [slug]
"""
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from sqlalchemy import select
from db import get_session
from db.models import Anime, Episode, DownloadLink


def inspect_anime(slug):
    """Tampilkan detail lengkap satu anime."""
    with get_session() as s:
        anime = s.execute(select(Anime).where(Anime.slug == slug)).scalar_one_or_none()
        if not anime:
            print(f"❌ Anime '{slug}' tidak ditemukan")
            return

        print("=" * 70)
        print(f"  🎬 {anime.title}")
        print("=" * 70)
        print(f"  ID          : {anime.id}")
        print(f"  Source      : {anime.source}")
        print(f"  Slug        : {anime.slug}")
        print(f"  URL         : {anime.url}")
        print(f"  Title JP    : {anime.title_jp}")
        print(f"  Studio      : {anime.studio}")
        print(f"  Producer    : {anime.producer}")
        print(f"  Type        : {anime.type}")
        print(f"  Status      : {anime.status}")
        print(f"  Duration    : {anime.duration}")
        print(f"  Release     : {anime.release_date}")
        print(f"  Total Ep    : {anime.total_episode}")
        print(f"  Rating      : {anime.rating}")
        print(f"  Poster      : {anime.poster_url}")
        print(f"  Genres      : {', '.join(anime.genres or [])}")
        print(f"  Scraped at  : {anime.scraped_at}")
        print(f"  Updated at  : {anime.updated_at}")
        print()
        print(f"  Sinopsis    : {(anime.synopsis or '')[:200]}...")

        # Episodes
        eps = list(s.execute(
            select(Episode).where(Episode.anime_id == anime.id)
            .order_by(Episode.episode_number.asc().nulls_last())
        ).scalars())

        print()
        print("=" * 70)
        print(f"  📺 EPISODES ({len(eps)})")
        print("=" * 70)

        for ep in eps:
            dls = list(s.execute(
                select(DownloadLink).where(DownloadLink.episode_id == ep.id)
            ).scalars())

            print(f"\n  ▶️  Ep #{ep.episode_number}: {ep.title}")
            print(f"      Slug     : {ep.slug}")
            print(f"      URL      : {ep.url}")
            print(f"      Stream   : {ep.stream_host} → {ep.stream_url[:60]}")
            print(f"      Downloads: {len(dls)}")

            by_quality = {}
            for d in dls:
                by_quality.setdefault(d.quality, []).append(d)

            for q, items in sorted(by_quality.items()):
                print(f"\n        📦 {q}")
                for d in items:
                    icon = "✅" if d.is_alive else "❌"
                    print(f"          {icon} {d.host:<12} → {d.final_host or '?'} "
                          f"({d.status or '-'})")


if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else None

    if slug:
        inspect_anime(slug)
    else:
        print("Usage: python -m control.inspect <slug>")
        print("Example: python -m control.inspect yowaki-max-sub-indo")