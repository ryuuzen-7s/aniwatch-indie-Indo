"""
security/deps.py — Auth dependencies untuk FastAPI.
"""
import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from db.database import SessionLocal
from .session import get_session, SESSION_COOKIE_NAME
from .api_key import verify_api_key


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  DB SESSION
# ═══════════════════════════════════════════════════════════
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  AUTH CONTEXT
# ═══════════════════════════════════════════════════════════
class AuthContext:
    """Info user yang sedang login."""

    def __init__(
        self,
        authenticated: bool = False,
        method: str = "",       # "api_key" | "session" | "none"
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        role: str = "anonymous",
        key_prefix: Optional[str] = None,
    ):
        self.authenticated = authenticated
        self.method = method
        self.user_id = user_id
        self.username = username
        self.role = role
        self.key_prefix = key_prefix

    def is_admin(self) -> bool:
        return self.role == "admin"


# ═══════════════════════════════════════════════════════════
#  OPTIONAL AUTH (tidak wajib)
# ═══════════════════════════════════════════════════════════
async def get_auth_optional(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> AuthContext:
    """
    Cek auth (opsional).
    Prioritas: API Key > Session Cookie.
    """
    ctx = AuthContext()

    # 1. Cek API key header
    if x_api_key:
        api_key = verify_api_key(db, x_api_key)
        if api_key:
            ctx.authenticated = True
            ctx.method = "api_key"
            ctx.user_id = api_key.user_id
            ctx.role = api_key.role
            ctx.key_prefix = api_key.key_prefix
            return ctx

    # 2. Cek session cookie
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        # Cek juga Authorization: Bearer <token>
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if token:
        session = get_session(token)
        if session:
            ctx.authenticated = True
            ctx.method = "session"
            ctx.user_id = session["user_id"]
            ctx.username = session["username"]
            ctx.role = session["role"]
            return ctx

    return ctx


# ═══════════════════════════════════════════════════════════
#  REQUIRED AUTH (wajib login)
# ═══════════════════════════════════════════════════════════
async def require_auth(
    ctx: AuthContext = Depends(get_auth_optional),
) -> AuthContext:
    """Wajib auth (API key atau session)."""
    if not ctx.authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentikasi diperlukan",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ctx


async def require_admin(
    ctx: AuthContext = Depends(require_auth),
) -> AuthContext:
    """Wajib admin."""
    if not ctx.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses admin diperlukan",
        )
    return ctx