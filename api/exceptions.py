"""
api/exceptions.py — Custom HTTP exceptions + handlers.
"""
import logging
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.fetcher import AllMirrorsFailedError, UnknownSourceError
from core.extractors import ParserNotFoundError, ParseError


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  CUSTOM EXCEPTIONS
# ═══════════════════════════════════════════════════════════
class AppError(Exception):
    """Base error aplikasi."""
    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "Terjadi kesalahan internal"

    def __init__(self, message: Optional[str] = None, details: Optional[dict] = None):
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    message = "Resource tidak ditemukan"


class AnimeNotFoundError(NotFoundError):
    code = "ANIME_NOT_FOUND"
    message = "Anime tidak ditemukan"


class EpisodeNotFoundError(NotFoundError):
    code = "EPISODE_NOT_FOUND"
    message = "Episode tidak ditemukan"


class BadRequestError(AppError):
    status_code = 400
    code = "BAD_REQUEST"
    message = "Request tidak valid"


class UpstreamError(AppError):
    status_code = 502
    code = "UPSTREAM_ERROR"
    message = "Server sumber sedang bermasalah"


class ScrapeError(AppError):
    status_code = 503
    code = "SCRAPE_ERROR"
    message = "Gagal scrape dari sumber"


# ═══════════════════════════════════════════════════════════
#  RESPONSE BUILDER
# ═══════════════════════════════════════════════════════════
def _error_response(
    code: str,
    message: str,
    status_code: int,
    details: Optional[dict] = None,
) -> JSONResponse:
    """Format response error standar."""
    from datetime import datetime, timezone
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "error": {
                "code": code,
                "message": message,
                "status": status_code,
                "details": details or {},
            },
        },
    )


# ═══════════════════════════════════════════════════════════
#  REGISTER HANDLERS
# ═══════════════════════════════════════════════════════════
def register_exception_handlers(app: FastAPI) -> None:
    """Daftarkan semua exception handler ke FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.warning(f"[{exc.code}] {exc.message} — {request.url.path}")
        return _error_response(exc.code, exc.message, exc.status_code, exc.details)

    @app.exception_handler(AnimeNotFoundError)
    async def anime_not_found_handler(request: Request, exc: AnimeNotFoundError):
        logger.info(f"Anime tidak ditemukan: {exc.details.get('slug')}")
        return _error_response(exc.code, exc.message, exc.status_code, exc.details)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Kalau detail adalah dict → pakai langsung
     if isinstance(exc.detail, dict):
        detail = exc.detail
        code = detail.get("code", f"HTTP_{exc.status_code}")
        message = detail.get("message", str(exc.detail))
        # Semua field lain jadi `details`
        extra_details = {k: v for k, v in detail.items() if k not in ("code", "message")}
        return _error_response(
            code=code,
            message=message,
            status_code=exc.status_code,
            details=extra_details,
        )

    # Default: string
     return _error_response(
         code=f"HTTP_{exc.status_code}",
         message=str(exc.detail),
         status_code=exc.status_code,
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return _error_response(
            code="VALIDATION_ERROR",
            message="Parameter tidak valid",
            status_code=422,
            details={"errors": exc.errors()},
        )

    # ─── Domain errors dari core ───
    @app.exception_handler(UnknownSourceError)
    async def unknown_source_handler(request: Request, exc: UnknownSourceError):
        return _error_response("UNKNOWN_SOURCE", str(exc), 400)

    @app.exception_handler(AllMirrorsFailedError)
    async def mirrors_failed_handler(request: Request, exc: AllMirrorsFailedError):
        return _error_response("ALL_MIRRORS_FAILED", str(exc), 502)

    @app.exception_handler(ParserNotFoundError)
    async def parser_not_found_handler(request: Request, exc: ParserNotFoundError):
        return _error_response("PARSER_NOT_FOUND", str(exc), 501)

    @app.exception_handler(ParseError)
    async def parse_error_handler(request: Request, exc: ParseError):
        return _error_response("PARSE_ERROR", str(exc), 502)

    # ─── Fallback ───
    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled error di {request.url.path}: {exc}")
        return _error_response(
            "INTERNAL_ERROR",
            "Terjadi kesalahan internal",
            500,
            details={"type": type(exc).__name__},
        )