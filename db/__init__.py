"""
db — Database layer untuk AniWatch.

Export:
- Engine, SessionLocal
- get_session, get_db
- init_db, reset_db, db_info, checkpoint_wal, vacuum_db
- Models: Base, Anime, Episode, DownloadLink, Report, User, ApiKey
- Repositories: AnimeRepository, EpisodeRepository, DownloadRepository, ReportRepository
- save_scrape_result, _extract_slug
- WriteLockContext, WRITE_LOCK, is_locked
"""
from .database import (
    engine,
    SessionLocal,
    get_session,
    get_db,
    init_db,
    reset_db,
    db_info,
    checkpoint_wal,
    vacuum_db,
)
from .models import (
    Base,
    Anime,
    Episode,
    DownloadLink,
    Report,
    User,
    ApiKey,
)
from .repository import (
    AnimeRepository,
    EpisodeRepository,
    DownloadRepository,
    ReportRepository,
    save_scrape_result,
    _extract_slug,
)
from .lock import (
    WRITE_LOCK,
    WriteLockContext,
    is_locked,
)


__all__ = [
    # Database
    "engine",
    "SessionLocal",
    "get_session",
    "get_db",
    "init_db",
    "reset_db",
    "db_info",
    "checkpoint_wal",
    "vacuum_db",

    # Models
    "Base",
    "Anime",
    "Episode",
    "DownloadLink",
    "Report",
    "User",
    "ApiKey",

    # Repositories
    "AnimeRepository",
    "EpisodeRepository",
    "DownloadRepository",
    "ReportRepository",
    "save_scrape_result",
    "_extract_slug",

    # Lock
    "WRITE_LOCK",
    "WriteLockContext",
    "is_locked",
]