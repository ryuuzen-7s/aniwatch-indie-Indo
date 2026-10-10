"""
api/routes/system.py — Endpoint sistem (/health, /stats, /).
"""
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select, func

from config import settings
from db import get_session, db_info
from db.models import Anime, Episode, DownloadLink, Report


router = APIRouter(tags=["system"])


@router.get("/", summary="Landing page")
async def root():
    """Landing page API."""
    return {
        "success": True,
        "data": {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "redoc": "/redoc",
            "monitor": "/monitor",
            "endpoints": [
                "GET  /share/anime/{slug}",
                "GET  /share/episodeid/{slug}",
                "GET  /share/episode/{number}/{slug}",
                "GET  /share/posterid/{slug}",
                "GET  /share/query?q=",
                "GET  /share/season/{season}",
                "GET  /share/now",
                "POST /share/errorid/{slug}",
                "POST /share/empty/{slug}",
                "POST /share/linkask/{slug}",
                "GET  /health",
                "GET  /stats",
            ],
        },
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat()},
        "error": None,
    }


@router.get("/health", summary="Cek status API")
async def health():
    """Cek status API."""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "name": settings.app_name,
            "version": settings.app_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat()},
        "error": None,
    }


@router.get("/stats", summary="Statistik DB")
async def stats():
    """Statistik database & sistem."""
    with get_session() as s:
        counts = {
            "anime": s.scalar(select(func.count()).select_from(Anime)) or 0,
            "episode": s.scalar(select(func.count()).select_from(Episode)) or 0,
            "download": s.scalar(select(func.count()).select_from(DownloadLink)) or 0,
            "report": s.scalar(select(func.count()).select_from(Report)) or 0,
        }

    info = db_info()

    return {
        "success": True,
        "data": {
            "database": {
                "path": info["path"],
                "size_kb": info["size_kb"],
                "wal_mode": info["wal_mode"],
            },
            "counts": counts,
            "sources": list(settings.sources.keys()),
            "default_source": settings.default_source,
        },
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat()},
        "error": None,
    }