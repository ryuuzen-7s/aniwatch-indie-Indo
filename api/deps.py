"""
api/deps.py — Dependency injection untuk FastAPI.
"""
from typing import Generator, Optional

from fastapi import Header, Query
from sqlalchemy.orm import Session

from db.database import SessionLocal
from config import settings


# ═══════════════════════════════════════════════════════════
#  DATABASE SESSION
# ═══════════════════════════════════════════════════════════
def get_db() -> Generator[Session, None, None]:
    """
    Dependency: session DB per-request.
    Auto-close setelah request selesai.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  COMMON PARAMS
# ═══════════════════════════════════════════════════════════
def common_source(
    source: Optional[str] = Query(
        None,
        description="Source anime: otakudesu | kuramanime | animeindo",
        examples=["otakudesu"],
    ),
) -> str:
    """Dependency: source query param dengan default."""
    return (source or settings.default_source).lower()


def common_refresh(
    refresh: bool = Query(
        False,
        description="Paksa re-scrape (abaikan cache & DB)",
    ),
) -> bool:
    """Dependency: flag force refresh."""
    return refresh