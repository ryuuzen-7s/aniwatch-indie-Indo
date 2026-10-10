"""
api/middleware/rate_limit.py — Middleware rate limiting untuk FastAPI.

Rate limit per API key (lookup dari DB), session, atau IP.
"""
import time
import hashlib
import logging
from typing import Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from security.rate_limit import (
    check_rate_limit,
    key_by_ip,
    key_by_api_key,
    LIMITS,
)


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  ENDPOINT YANG DI-EXCLUDE
# ═══════════════════════════════════════════════════════════
EXCLUDED_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/health",
    "/monitor",
    "/monitor/static",
    "/md",
    "/portal",
    "/portal/static",
    "/portal/assets",
    "/portal/docs",
    "/error",
}

# Endpoint auth yang lebih ketat
AUTH_PATHS = {
    "/login",
    "/register",
    "/get-key",
}


# ═══════════════════════════════════════════════════════════
#  LOOKUP API KEY RATE LIMIT (dengan cache)
# ═══════════════════════════════════════════════════════════
_LIMIT_CACHE: dict = {}
_LIMIT_CACHE_TTL = 60  # detik


def _lookup_api_key_limit(raw_key: str) -> Optional[int]:
    """
    Lookup rate_limit dari DB berdasarkan API key.
    Cached 60s untuk performa.
    """
    try:
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        # Cek cache
        cached = _LIMIT_CACHE.get(key_hash)
        if cached:
            limit, expires = cached
            if time.time() < expires:
                return limit

        # Lookup DB
        from db.database import SessionLocal
        from db.models import ApiKey
        from sqlalchemy import select

        with SessionLocal() as db:
            api_key = db.execute(
                select(ApiKey).where(ApiKey.key_hash == key_hash)
            ).scalar_one_or_none()

            if api_key and api_key.is_active:
                limit = api_key.rate_limit
                _LIMIT_CACHE[key_hash] = (limit, time.time() + _LIMIT_CACHE_TTL)
                return limit
    except Exception as e:
        logger.debug(f"[RateLimit] Lookup error: {e}")

    return None


# ═══════════════════════════════════════════════════════════
#  CLIENT IP
# ═══════════════════════════════════════════════════════════
def _get_client_ip(request: Request) -> str:
    """Ambil IP client."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host

    return "unknown"


# ═══════════════════════════════════════════════════════════
#  LIMIT TYPE
# ═══════════════════════════════════════════════════════════
def _get_limit_type(request: Request) -> tuple:
    """
    Tentukan key + limit type + override_max.
    Return: (key, limit_type, override_max)
    """
    ip = _get_client_ip(request)
    path = request.url.path

    # 1. Endpoint auth → sangat ketat (per IP)
    if path in AUTH_PATHS:
        return key_by_ip(ip, "auth"), "auth", None

    # 2. API key header → lookup rate_limit dari DB
    api_key = request.headers.get("x-api-key")
    if api_key and api_key.startswith("anw_"):
        prefix = api_key[:12]
        override = _lookup_api_key_limit(api_key)
        return key_by_api_key(prefix), "api_key", override

    # 3. Session cookie
    session_token = request.cookies.get("aniwatch_session")
    if session_token:
        return f"session:{session_token[:12]}", "session", None

    # 4. Anonymous by IP
    return key_by_ip(ip, "general"), "anonymous", None


# ═══════════════════════════════════════════════════════════
#  MIDDLEWARE
# ═══════════════════════════════════════════════════════════
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware rate limiting."""

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next):
        # Skip kalau disabled
        if not self.enabled:
            return await call_next(request)

        # Skip excluded paths
        path = request.url.path
        if path in EXCLUDED_PATHS or path.startswith("/monitor/static"):
            return await call_next(request)

        # Skip OPTIONS (preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Cek limit
        key, limit_type, override_max = _get_limit_type(request)

        allowed, info = check_rate_limit(
            key=key,
            limit_type=limit_type,
            override_max=override_max,
        )

        # Headers standar
        headers = {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(info["reset_at"]),
        }

        if not allowed:
            logger.warning(
                f"[RateLimit] {key} ({limit_type}) exceeded — "
                f"limit={info['limit']}/{info['window']}s"
            )
            headers["Retry-After"] = str(info["reset_in"])
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "data": None,
                    "meta": {"timestamp": info["reset_at"]},
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": (
                            f"Terlalu banyak request. "
                            f"Coba lagi dalam {info['reset_in']} detik."
                        ),
                        "status": 429,
                        "details": {
                            "limit": info["limit"],
                            "window": info["window"],
                            "retry_after": info["reset_in"],
                        },
                    },
                },
                headers=headers,
            )

        # Lanjut + tambah headers
        response = await call_next(request)
        for k, v in headers.items():
            response.headers[k] = v

        return response


# ═══════════════════════════════════════════════════════════
#  HELPER
# ═══════════════════════════════════════════════════════════
def add_rate_limit_headers(response: Response, info: dict) -> None:
    """Tambah header rate limit ke response."""
    response.headers["X-RateLimit-Limit"] = str(info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(info["reset_at"])