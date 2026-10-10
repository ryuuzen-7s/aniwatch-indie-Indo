"""api.routes - FastAPI routers."""
from .anime import router as anime_router
from .episode import router as episode_router
from .search import router as search_router
from .poster import router as poster_router
from .season import router as season_router
from .now import router as now_router
from .reports import router as reports_router
from .empty import router as empty_router
from .linkask import router as linkask_router
from .system import router as system_router
from .auth import router as auth_router

__all__ = [
    "anime_router",
    "episode_router",
    "search_router",
    "poster_router",
    "season_router",
    "now_router",
    "reports_router",
    "empty_router",
    "linkask_router",
    "system_router",
    "auth_router",
]
