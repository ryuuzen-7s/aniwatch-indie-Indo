"""
security/login.py — Login, logout, register.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import User
from .password import hash_password, verify_password
from .session import create_session, delete_session


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  USER LOOKUP
# ═══════════════════════════════════════════════════════════
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Cari user by username."""
    return db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Cari user by id."""
    return db.get(User, user_id)


# ═══════════════════════════════════════════════════════════
#  REGISTER
# ═══════════════════════════════════════════════════════════
def register_user(
    db: Session,
    username: str,
    password: str,
    email: str = "",
    role: str = "user",
) -> Tuple[Optional[User], Optional[str]]:
    """
    Register user baru.
    Return: (user, error)
    """
    # Validasi username
    username = username.strip().lower()
    if not username or len(username) < 3 or len(username) > 50:
        return None, "Username harus 3-50 karakter"

    if not username.replace("_", "").replace("-", "").isalnum():
        return None, "Username hanya boleh huruf, angka, _ dan -"

    # Cek existing
    if get_user_by_username(db, username):
        return None, "Username sudah digunakan"

    # Validasi password
    if len(password) < 6:
        return None, "Password minimal 6 karakter"

    # Hash password
    password_hash = hash_password(password)

    user = User(
        username=username,
        password_hash=password_hash,
        email=email,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()

    logger.info(f"👤 User baru: {username}")
    return user, None


# ═══════════════════════════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════════════════════════
def login_user(
    db: Session,
    username: str,
    password: str,
    ip: str = "",
    user_agent: str = "",
) -> Tuple[Optional[dict], Optional[str]]:
    """
    Login user.
    Return: (session_data, error)
    """
    username = username.strip().lower()

    user = get_user_by_username(db, username)
    if not user:
        # Delay to prevent timing attack
        verify_password("dummy", "$2b$12$dummy")
        return None, "Username atau password salah"

    if not user.is_active:
        return None, "Akun tidak aktif"

    if not verify_password(password, user.password_hash):
        logger.warning(f"Login gagal: {username} dari {ip}")
        return None, "Username atau password salah"

    # Update last_login
    user.last_login = datetime.now(timezone.utc)
    db.flush()

    # Buat session
    token = create_session(
        user_id=user.id,
        username=user.username,
        role=user.role,
        ip=ip,
        user_agent=user_agent,
    )

    logger.info(f"✅ Login sukses: {username}")

    return {
        "token": token,
        "user": user.to_dict(),
    }, None


# ═══════════════════════════════════════════════════════════
#  LOGOUT
# ═══════════════════════════════════════════════════════════
def logout_user(token: str) -> bool:
    """Logout user."""
    return delete_session(token)