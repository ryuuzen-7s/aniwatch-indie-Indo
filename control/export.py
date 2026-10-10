"""
control/export.py — Export DB ke JSON.

Jalankan:
    python -m control.export                       # semua anime
    python -m control.export yowaki-max-sub-indo   # 1 anime
    python -m control.export --format csv
"""
import sys
import json
import csv
from pathlib import Path
from datetime import datetime

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from sqlalchemy import select
from db import get_session
from db.models import Anime, Episode, DownloadLink


OUT = Path("control/exports")
OUT.mkdir(parents=True, exist_ok=True)


def export_anime(anime, s):
    """Export 1 anime → dict."""
    eps = list(s.execute(
        select(Episode).where(Episode.anime_id == anime.id)
    ).scalars())

    episode_details = []
    for ep in eps:
        dls = list(s.execute(
            select(DownloadLink).where(DownloadLink.episode_id == ep.id)
        ).scalars())

        episode_details.append({
            "url": ep.url,
            "title": ep.title,
            "episode_number": ep.episode_number,
            "streams": [{
                "host": ep.stream_host,
                "url": ep.stream_url,
            }] if ep.stream_url else [],
            "downloads": [d.to_dict() for d in dls],
        })

    return {
        "source": anime.source,
        "url": anime.url,
        "slug": anime.slug,
        "scraped_at": anime.scraped_at.isoformat() if anime.scraped_at else None,
        "metadata": {
            "title": anime.title,
            "title_jp": anime.title_jp,
            "synopsis": anime.synopsis,
            "poster": anime.poster_url,
            "studio": anime.studio,
            "producer": anime.producer,
            "type": anime.type,
            "status": anime.status,
            "duration": anime.duration,
            "release_date": anime.release_date,
            "total_episode": anime.total_episode,
            "rating": anime.rating,
            "genres": anime.genres or [],
            "info": anime.info or {},
        },
        "episode_details": episode_details,
    }


def main():
    args = sys.argv[1:]
    slug_filter = None
    fmt = "json"

    for i, a in enumerate(args):
        if a == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
        elif not a.startswith("--"):
            slug_filter = a

    print("=" * 62)
    print("  📤 EXPORT DATABASE")
    print("=" * 62)

    with get_session() as s:
        if slug_filter:
            animes = [s.execute(select(Anime).where(Anime.slug == slug_filter)).scalar_one_or_none()]
            animes = [a for a in animes if a]
        else:
            animes = list(s.execute(select(Anime)).scalars())

        if not animes:
            print("  ❌ Tidak ada anime untuk di-export")
            return

        print(f"  📚 {len(animes)} anime akan di-export\n")

        all_data = []
        for anime in animes:
            data = export_anime(anime, s)
            all_data.append(data)
            print(f"  ✅ {anime.slug}")

        # Save
        if fmt == "json":
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_file = OUT / f"export_{ts}.json"
            out_file.write_text(
                json.dumps(all_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"\n  💾 Saved: {out_file}")
        elif fmt == "csv":
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_file = OUT / f"export_{ts}.csv"
            with open(out_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["slug", "title", "episode", "quality", "host", "url", "alive"])
                for a in all_data:
                    for ep in a["episode_details"]:
                        for d in ep["downloads"]:
                            writer.writerow([
                                a["slug"], a["metadata"]["title"],
                                ep["episode_number"], d["quality"], d["host"],
                                d["final_url"] or d["url"], d["is_alive"],
                            ])
            print(f"\n  💾 Saved: {out_file}")


if __name__ == "__main__":
    main()