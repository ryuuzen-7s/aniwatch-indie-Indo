"""api/routes/auth.py - Endpoint auth."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from security.deps import get_db, get_auth_optional, require_auth, AuthContext
from security.login import login_user, logout_user, register_user
from security.api_key import generate_api_key, list_api_keys, revoke_api_key
from security.session import (
    SESSION_COOKIE_NAME,
    session_store,
    delete_session,
)
from security.models import (
    LoginRequest,
    RegisterRequest,
    GetKeyRequest,
)
from api.models.common import success_response


logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


@router.post("/login", summary="Login user")
async def login_endpoint(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else ""
    ua = request.headers.get("user-agent", "")

    session_data, error = login_user(
        db, body.username, body.password, ip=ip, user_agent=ua,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
        )

    db.commit()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_data["token"],
        max_age=86400,
        httponly=True,
        samesite="lax",
        secure=False,
    )

    return success_response(
        data=session_data,
        cached=False,
        source="db",
    )


@router.post("/logout", summary="Logout user")
async def logout_endpoint(
    request: Request,
    response: Response,
    ctx: AuthContext = Depends(require_auth),
):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if token:
        delete_session(token)

    response.delete_cookie(SESSION_COOKIE_NAME)

    return success_response(
        data={"message": "Logout sukses"},
        cached=False,
        source="db",
    )


@router.post(
    "/register",
    summary="Register user baru",
    status_code=status.HTTP_201_CREATED,
)
async def register_endpoint(
    body: RegisterRequest,
    db: Session = Depends(get_db),
):
    user, error = register_user(
        db,
        username=body.username,
        password=body.password,
        email=body.email,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    db.commit()
    db.refresh(user)

    return success_response(
        data=user.to_dict(),
        cached=False,
        source="db",
    )


@router.post("/get-key", summary="Generate API key")
async def get_key_endpoint(
    body: GetKeyRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_optional),
    db: Session = Depends(get_db),
):
    """Generate API key. Prioritas user_id: session -> body -> anonymous."""
    user_id = None
    role = "user"

    # 1. PRIORITAS: session / Bearer
    if ctx.authenticated and ctx.user_id:
        user_id = ctx.user_id
        role = "user"
        logger.info(f"Get-key: bind ke user_id={user_id} (session)")

    # 2. FALLBACK: body username + password
    elif body.username and body.password:
        from security.login import get_user_by_username
        from security.password import verify_password

        user = get_user_by_username(db, body.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username atau password salah",
            )
        if not verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username atau password salah",
            )
        user_id = user.id
        logger.info(f"Get-key: bind ke user_id={user_id} (body)")

    # 3. Anonymous
    else:
        logger.info("Get-key: anonymous (user_id=None)")

    result = generate_api_key(
        db,
        name=body.name,
        user_id=user_id,
        role=role,
        rate_limit=body.rate_limit,
        expires_days=body.expires_days,
        max_requests=getattr(body, "max_requests", None),
    )

    db.commit()

    return success_response(
        data=result,
        cached=False,
        source="db",
    )


@router.get("/me", summary="Info user sekarang")
async def me_endpoint(
    ctx: AuthContext = Depends(get_auth_optional),
):
    return success_response(
        data={
            "authenticated": ctx.authenticated,
            "method": ctx.method,
            "user_id": ctx.user_id,
            "username": ctx.username,
            "role": ctx.role,
            "key_prefix": ctx.key_prefix,
        },
        cached=False,
        source="memory",
    )


@router.get("/keys", summary="List API key")
async def list_keys_endpoint(
    ctx: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """List API key user. Admin bisa lihat semua."""
    # WAJIB: user_id harus ada (kecuali admin)
    if ctx.user_id is None and not ctx.is_admin():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session tidak valid, silakan login ulang",
        )

    if ctx.is_admin():
        keys = list_api_keys(db, user_id=None)
    else:
        keys = list_api_keys(db, user_id=ctx.user_id)

    return success_response(
        data=[k.to_dict() for k in keys],
        cached=False,
        source="db",
    )


@router.delete("/keys/{key_id}", summary="Revoke API key")
async def revoke_key_endpoint(
    key_id: int,
    ctx: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    from db.models import ApiKey

    key = db.get(ApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key tidak ditemukan")

    if not ctx.is_admin() and key.user_id != ctx.user_id:
        raise HTTPException(
            status_code=403,
            detail="Tidak boleh revoke key orang lain",
        )

    ok = revoke_api_key(db, key_id)
    db.commit()

    return success_response(
        data={"revoked": ok, "key_id": key_id},
        cached=False,
        source="db",
    )


@router.get(
    "/session/stats",
    summary="Statistik session",
    include_in_schema=False,
)
async def session_stats_endpoint():
    return success_response(
        data=session_store.stats(),
        cached=False,
        source="memory",
    )
