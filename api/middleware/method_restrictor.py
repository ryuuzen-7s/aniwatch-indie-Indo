"""
api/middleware/method_restrictor.py — Middleware pembatas HTTP method.

Hanya GET & POST yang diizinkan (default).
OPTIONS & HEAD selalu lolos (CORS preflight, health check).
Path di `excluded_paths` dilewati (mis. /keys untuk DELETE).

Error response otomatis di-format oleh handler
`StarletteHTTPException` di `api/exceptions.py`.
"""
import logging
from typing import Iterable, Set

from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


logger = logging.getLogger(__name__)


# ─── Default (bisa di-override lewat .env) ───
DEFAULT_ALLOWED: Set[str] = {"GET", "POST"}
DEFAULT_EXCLUDED: tuple[str, ...] = (
    "/keys",          # DELETE /keys/{id} (portal)
    "/docs",
    "/redoc",
    "/openapi.json",
    "/monitor",
    "/monitor/static",
)
ALWAYS_ALLOWED: Set[str] = {"OPTIONS", "HEAD"}


class MethodRestrictorMiddleware(BaseHTTPMiddleware):
    """
    Batasi HTTP method ke `allowed_methods` untuk semua request,
    kecuali path di `excluded_paths`.

    Usage:
        app.add_middleware(
            MethodRestrictorMiddleware,
            allowed_methods={"GET", "POST"},
            excluded_paths=("/keys",),
        )
    """

    def __init__(
        self,
        app,
        allowed_methods: Iterable[str] | None = None,
        excluded_paths: Iterable[str] | None = None,
        enabled: bool = True,
    ):
        super().__init__(app)
        self.enabled = enabled
        self.allowed_methods: Set[str] = {
            m.strip().upper()
            for m in (allowed_methods or DEFAULT_ALLOWED)
            if m and m.strip()
        }
        self.excluded_paths: tuple[str, ...] = tuple(
            p.strip() for p in (excluded_paths or DEFAULT_EXCLUDED)
            if p and p.strip()
        )

    def _is_excluded(self, path: str) -> bool:
        """Cek apakah path dikecualikan (prefix match)."""
        return any(path.startswith(p) for p in self.excluded_paths)

    async def dispatch(self, request: Request, call_next):
        # 0. Kalau disabled, skip
        if not self.enabled:
            return await call_next(request)

        path = request.url.path
        method = request.method.upper()

        # 1. Skip path yang di-exclude
        if self._is_excluded(path):
            return await call_next(request)

        # 2. OPTIONS & HEAD selalu lolos
        if method in ALWAYS_ALLOWED:
            return await call_next(request)

        # 3. Cek method
        if method not in self.allowed_methods:
            logger.warning(
                f"[MethodRestrictor] Tolak {method} {path} "
                f"(allowed: {sorted(self.allowed_methods)})"
            )
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail=(
                    f"Method {method} tidak diizinkan pada endpoint ini. "
                    f"Hanya {sorted(self.allowed_methods)} yang diperbolehkan."
                ),
                headers={
                    "Allow": ", ".join(sorted(self.allowed_methods)),
                },
            )

        # 4. Lanjut
        return await call_next(request)