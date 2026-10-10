"""
db/repository.py — CRUD operations untuk AniWatch.

Fitur:
- Retry otomatis pada database locked
- Global write lock untuk cegah 2 writer
"""
import re
import time
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .database import get_session
from .lock import WriteLockContext
from .models import Anime, Episode, DownloadLink, Report


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════
MAX_RETRIES = 5
RETRY_BASE_DELAY = 0.5  # detik


# ═══════════════════════════════════════════════════════════
#  RETRY DECORATOR
# ═══════════════════════════════════════════════════════════
def with_retry(func):
    """
    Decorator: retry pada OperationalError 'database is locked'.

    Usage:
        @with_retry
        def some_write_operation():
            ...
    """
    def wrapper(*args, **kwargs):
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                if "database is locked" in str(e).lower():
                    last_error = e
                    if attempt < MAX_RETRIES - 1:
                        wait = RETRY_BASE_DELAY * (2 ** attempt)
                        logger.warning(
                            f"[Retry] {func.__name__}: DB locked, "
                            f"attempt {attempt + 1}/{MAX_RETRIES}, wait {wait:.1f}s"
                        )
                        time.sleep(wait)
                        continue
                    else:
                        logger.error(
                            f"[Retry] {func.__name__}: DB locked {MAX_RETRIES}x, give up"
                        )
                raise
        if last_error:
            raise last_error
    return wrapper


# ═══════════════════════════════════════════════════════════
#  ANIME REPOSITORY
# ═══════════════════════════════════════════════════════════
class AnimeRepository:

    @staticmethod
    def get_by_slug(session: Session, slug: str) -> Optional[Anime]:
        return session.execute(
            select(Anime).where(Anime.slug == slug)
        ).scalar_one_or_none()

    @staticmethod
    def get_by_id(session: Session, anime_id: int) -> Optional[Anime]:
        return session.get(Anime, anime_id)

    @staticmethod
    def list_all(session: Session, limit: int = 50, offset: int = 0) -> List[Anime]:
        return list(session.execute(
            select(Anime).order_by(Anime.updated_at.desc()).limit(limit).offset(offset)
        ).scalars())

    @staticmethod
    def count(session: Session) -> int:
        return session.scalar(select(func.count()).select_from(Anime)) or 0

    @staticmethod
    def upsert(session: Session, data: Dict[str, Any]) -> Anime:
        slug = data.get("slug")
        if not slug:
            raise ValueError("Anime.slug wajib ada")

        existing = AnimeRepository.get_by_slug(session, slug)

        if existing:
            for key, value in data.items():
                if key in ("id", "scraped_at"):
                    continue
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.now(timezone.utc)
            return existing
        else:
            anime = Anime(**{k: v for k, v in data.items() if hasattr(Anime, k)})
            session.add(anime)
            session.flush()
            return anime

    @staticmethod
    def delete_by_slug(session: Session, slug: str) -> bool:
        anime = AnimeRepository.get_by_slug(session, slug)
        if not anime:
            return False
        session.delete(anime)
        return True


# ═══════════════════════════════════════════════════════════
#  EPISODE REPOSITORY
# ═══════════════════════════════════════════════════════════
class EpisodeRepository:

    @staticmethod
    def get_by_slug(session: Session, slug: str) -> Optional[Episode]:
        return session.execute(
            select(Episode).where(Episode.slug == slug)
        ).scalar_one_or_none()

    @staticmethod
    def list_by_anime(session: Session, anime_id: int) -> List[Episode]:
        return list(session.execute(
            select(Episode)
            .where(Episode.anime_id == anime_id)
            .order_by(Episode.episode_number.asc().nulls_last())
        ).scalars())

    @staticmethod
    def get_by_number(session: Session, anime_id: int, number: int) -> Optional[Episode]:
        return session.execute(
            select(Episode)
            .where(Episode.anime_id == anime_id)
            .where(Episode.episode_number == number)
        ).scalar_one_or_none()

    @staticmethod
    def upsert(session: Session, data: Dict[str, Any]) -> Episode:
        slug = data.get("slug")
        if not slug:
            raise ValueError("Episode.slug wajib ada")
        if not data.get("anime_id"):
            raise ValueError("Episode.anime_id wajib ada")

        existing = EpisodeRepository.get_by_slug(session, slug)

        if existing:
            for key, value in data.items():
                if key in ("id", "scraped_at"):
                    continue
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.now(timezone.utc)
            return existing
        else:
            episode = Episode(**{k: v for k, v in data.items() if hasattr(Episode, k)})
            session.add(episode)
            session.flush()
            return episode


# ═══════════════════════════════════════════════════════════
#  DOWNLOAD REPOSITORY
# ═══════════════════════════════════════════════════════════
class DownloadRepository:

    @staticmethod
    def list_by_episode(
        session: Session,
        episode_id: int,
        only_alive: bool = False,
    ) -> List[DownloadLink]:
        stmt = select(DownloadLink).where(DownloadLink.episode_id == episode_id)
        if only_alive:
            stmt = stmt.where(DownloadLink.is_alive.is_(True))
        return list(session.execute(stmt).scalars())

    @staticmethod
    def get_by_key(
        session: Session,
        episode_id: int,
        quality: str,
        host: str,
    ) -> Optional[DownloadLink]:
        return session.execute(
            select(DownloadLink)
            .where(DownloadLink.episode_id == episode_id)
            .where(DownloadLink.quality == quality)
            .where(DownloadLink.host == host)
        ).scalar_one_or_none()

    @staticmethod
    def upsert(session: Session, data: Dict[str, Any]) -> DownloadLink:
        episode_id = data.get("episode_id")
        quality = data.get("quality", "")
        host = data.get("host", "")

        if not episode_id:
            raise ValueError("DownloadLink.episode_id wajib ada")

        existing = DownloadRepository.get_by_key(session, episode_id, quality, host)

        if existing:
            for key, value in data.items():
                if key in ("id", "created_at"):
                    continue
                if hasattr(existing, key):
                    setattr(existing, key, value)
            return existing
        else:
            link = DownloadLink(**{k: v for k, v in data.items() if hasattr(DownloadLink, k)})
            session.add(link)
            session.flush()
            return link

    @staticmethod
    def mark_checked(
        session: Session,
        link_id: int,
        is_alive: bool,
        status: Optional[int] = None,
        error: str = "",
    ) -> None:
        session.execute(
            update(DownloadLink)
            .where(DownloadLink.id == link_id)
            .values(
                is_alive=is_alive,
                status=status,
                error=error[:255],
                checked_at=datetime.now(timezone.utc),
            )
        )


# ═══════════════════════════════════════════════════════════
#  REPORT REPOSITORY
# ═══════════════════════════════════════════════════════════
class ReportRepository:

    @staticmethod
    def create(session: Session, data: Dict[str, Any]) -> Report:
        report = Report(**{k: v for k, v in data.items() if hasattr(Report, k)})
        session.add(report)
        session.flush()
        return report

    @staticmethod
    def list_recent(
        session: Session,
        limit: int = 50,
        only_unresolved: bool = False,
    ) -> List[Report]:
        stmt = select(Report).order_by(Report.created_at.desc()).limit(limit)
        if only_unresolved:
            stmt = stmt.where(Report.resolved.is_(False))
        return list(session.execute(stmt).scalars())

    @staticmethod
    def count_unresolved(session: Session) -> int:
        return session.scalar(
            select(func.count()).select_from(Report).where(Report.resolved.is_(False))
        ) or 0


# ═══════════════════════════════════════════════════════════
#  SLUG EXTRACTOR
# ═══════════════════════════════════════════════════════════
def _extract_slug(result: Dict[str, Any]) -> str:
    """Auto-extract slug dari berbagai format JSON."""
    if result.get("slug"):
        return result["slug"]

    url = result.get("url") or ""
    if not url:
        src = result.get("source", "")
        if isinstance(src, str) and src.startswith("http"):
            url = src

    if url:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        if path:
            slug = path.split("/")[-1]
            if slug:
                return slug

    title = (result.get("metadata", {}) or {}).get("title", "")
    if title:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        if slug:
            return slug

    raise ValueError("Tidak bisa extract slug dari result")


# ═══════════════════════════════════════════════════════════
#  SAVE SCRAPE RESULT (dengan retry + write lock)
# ═══════════════════════════════════════════════════════════
@with_retry
def save_scrape_result(result: Dict[str, Any]) -> Dict[str, int]:
    """
    Simpan hasil scrape ke database.

    Fitur:
    - Retry otomatis pada database locked (max 5x)
    - Global write lock → cegah 2 writer
    """
    counters = {"anime": 0, "episodes": 0, "downloads": 0}

    meta = result.get("metadata", {}) or {}
    if not meta.get("title"):
        raise ValueError("metadata.title kosong — data tidak valid.")

    slug = _extract_slug(result)

    source = result.get("source", "otakudesu")
    if isinstance(source, str) and source.startswith("http"):
        domain = urlparse(source).netloc.lower()
        if "otakudesu" in domain:
            source = "otakudesu"
        elif "kuramanime" in domain:
            source = "kuramanime"
        elif "anime-indo" in domain or "animeindo" in domain:
            source = "animeindo"
        else:
            source = domain.split(".")[0]

    url = result.get("url") or ""
    if not url and isinstance(result.get("source", ""), str) and result["source"].startswith("http"):
        url = result["source"]

    # ─── Acquire global write lock ───
    with WriteLockContext(timeout=30.0):
        with get_session() as session:
            anime_data = {
                "source": source,
                "slug": slug,
                "url": url,
                "title": meta.get("title") or "",
                "title_jp": meta.get("title_jp") or "",
                "synopsis": meta.get("synopsis") or "",
                "poster_url": meta.get("poster") or "",
                "studio": meta.get("studio") or "",
                "producer": meta.get("producer") or "",
                "type": meta.get("type") or "",
                "status": meta.get("status") or "",
                "duration": meta.get("duration") or "",
                "release_date": meta.get("release_date") or "",
                "total_episode": meta.get("total_episode"),
                "rating": meta.get("rating"),
                "genres": meta.get("genres") or [],
                "info": meta.get("info") or {},
            }
            anime = AnimeRepository.upsert(session, anime_data)
            counters["anime"] = 1

            for ep_data in result.get("episode_details", []):
                streams = ep_data.get("streams", [])
                stream_url = streams[0]["url"] if streams else ""
                stream_host = streams[0]["host"] if streams else ""

                ep_slug = ep_data.get("slug") or ""
                if not ep_slug:
                    ep_url = ep_data.get("url", "")
                    if ep_url:
                        ep_slug = ep_url.rstrip("/").split("/")[-1]
                    else:
                        ep_title = ep_data.get("title") or "episode"
                        ep_slug = re.sub(r"[^a-z0-9]+", "-", ep_title.lower()).strip("-")

                episode_data = {
                    "anime_id": anime.id,
                    "slug": ep_slug,
                    "url": ep_data.get("url", ""),
                    "title": ep_data.get("title") or "",
                    "episode_number": ep_data.get("episode_number"),
                    "stream_url": stream_url,
                    "stream_host": stream_host,
                }
                episode = EpisodeRepository.upsert(session, episode_data)
                counters["episodes"] += 1

                for dl_data in ep_data.get("downloads", []):
                    dl = {
                        "episode_id": episode.id,
                        "quality": dl_data.get("quality") or "",
                        "host": dl_data.get("host") or "",
                        "url": dl_data.get("url") or "",
                        "final_url": dl_data.get("final_url") or "",
                        "final_host": dl_data.get("final_host") or "",
                        "status": dl_data.get("status"),
                        "is_alive": bool(dl_data.get("alive", True)),
                        "error": (dl_data.get("error") or "")[:255],
                        "checked_at": datetime.now(timezone.utc),
                    }
                    DownloadRepository.upsert(session, dl)
                    counters["downloads"] += 1

    logger.info(
        f"[Save] {slug}: {counters['anime']} anime, "
        f"{counters['episodes']} ep, {counters['downloads']} dl"
    )

    return counters