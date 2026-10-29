"""
api/middleware/method_restrictor.py — Middleware pembatas HTTP method.
"""
import logging
from typing import Iterable, Set

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


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

        # 2. OPTIONS & HEAD selalu lolos (CORS preflight & health check)
        if method in ALWAYS_ALLOWED:
            return await call_next(request)

        # 3. Cek method
        if method not in self.allowed_methods:
            logger.warning(
                f"[MethodRestrictor] Tolak {method} {path} "
                f"(allowed: {sorted(self.allowed_methods)})"
            )
            
            # ⚠️ GUNAKAN JSONResponse, JANGAN raise HTTPException
            return JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content={
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "HTTP_405",
                        "message": (
                            f"Method {method} tidak diizinkan pada endpoint ini. "
                            f"Hanya {sorted(self.allowed_methods)} yang diperbolehkan."
                        ),
                        "status": 405,
                        "details": {}
                    }
                },
                headers={
                    "Allow": ", ".join(sorted(self.allowed_methods)),
                }
            )

        # 4. Lanjut
        return await call_next(request)