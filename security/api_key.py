"""security/api_key.py - Generate & verify API key."""
import logging
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from db import get_session
from db.models import ApiKey


logger = logging.getLogger(__name__)


API_KEY_PREFIX = "anw_"
API_KEY_BODY_LEN = 40


def _generate_key() -> str:
    body = secrets.token_urlsafe(API_KEY_BODY_LEN)[:API_KEY_BODY_LEN]
    return API_KEY_PREFIX + body


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _key_prefix(key: str, length: int = 12) -> str:
    return key[:length]


def generate_api_key(
    db: Session,
    name: str = "default",
    user_id: Optional[int] = None,
    role: str = "user",
    rate_limit: int = 100,
    expires_days: Optional[int] = None,
    max_requests: Optional[int] = None,
) -> dict:
    raw_key = _generate_key()
    key_hash = _hash_key(raw_key)
    prefix = _key_prefix(raw_key)

    expires_at = None
    if expires_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

    api_key = ApiKey(
        key_hash=key_hash,
        key_prefix=prefix,
        name=name,
        user_id=user_id,
        role=role,
        rate_limit=rate_limit,
        expires_at=expires_at,
        is_active=True,
    )

    # Set max_requests kalau field ada di model
    if hasattr(api_key, "max_requests"):
        api_key.max_requests = max_requests

    db.add(api_key)
    db.flush()

    logger.info("API key baru: " + prefix + "... (" + name + ")")

    return {
        "key": raw_key,
        "info": api_key.to_dict(),
    }


def verify_api_key(db: Session, raw_key: str, retries: int = 3) -> Optional[ApiKey]:
    """Verify API key dengan retry saat DB locked."""
    import time
    from sqlalchemy.exc import OperationalError
    from sqlalchemy import update

    if not raw_key or not raw_key.startswith(API_KEY_PREFIX):
        return None

    key_hash = _hash_key(raw_key)

    api_key = db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash)
    ).scalar_one_or_none()

    if not api_key:
        return None

    if not api_key.is_active:
        return None

    if api_key.expires_at:
        exp = api_key.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > exp:
            return None

    # Update counter via SQL langsung (retry saat locked)
    for attempt in range(retries):
        try:
            db.execute(
                update(ApiKey)
                .where(ApiKey.id == api_key.id)
                .values(
                    request_count=ApiKey.request_count + 1,
                    last_used=datetime.now(timezone.utc),
                )
            )
            db.flush()
            break
        except OperationalError as e:
            if "database is locked" in str(e).lower():
                db.rollback()
                if attempt < retries - 1:
                    time.sleep(0.2 * (attempt + 1))
                    continue
                else:
                    logger.warning(f"verify_api_key: DB locked {retries}x, skip update")
            else:
                raise

    return api_key


def revoke_api_key(db: Session, key_id: int) -> bool:
    api_key = db.get(ApiKey, key_id)
    if not api_key:
        return False
    api_key.is_active = False
    db.flush()
    return True


def list_api_keys(db: Session, user_id: Optional[int] = None) -> List[ApiKey]:
    stmt = select(ApiKey).order_by(ApiKey.created_at.desc())
    if user_id:
        stmt = stmt.where(ApiKey.user_id == user_id)
    return list(db.execute(stmt).scalars())
