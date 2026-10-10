"""security/password.py - Hash & verify password (SHA-256)."""
import logging
import secrets
import hashlib


logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return "sha256$" + salt + "$" + h


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        parts = password_hash.split("$")
        if len(parts) != 3 or parts[0] != "sha256":
            try:
                import bcrypt
                return bcrypt.checkpw(
                    password.encode("utf-8"),
                    password_hash.encode("utf-8"),
                )
            except Exception:
                return False
        _, salt, expected = parts
        h = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
        return secrets.compare_digest(h, expected)
    except Exception as e:
        logger.warning("Password verify error: " + str(e))
        return False


def generate_password(length: int = 16) -> str:
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))
