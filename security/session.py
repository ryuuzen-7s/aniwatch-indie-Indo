"""
security/session.py — Session in-memory dengan TTL.

Session untuk login via browser/API. Simpel, tidak butuh Redis.
"""
import time
import logging
import secrets
import threading
from typing import Optional, Dict
from collections import OrderedDict


logger = logging.getLogger(__name__)


SESSION_TTL = 86400  # 24 jam
SESSION_MAX = 1000   # Max session aktif
SESSION_COOKIE_NAME = "aniwatch_session"


class SessionStore:
    """Session in-memory dengan TTL."""

    def __init__(self, max_size: int = SESSION_MAX, ttl: int = SESSION_TTL):
        self.max_size = max_size
        self.ttl = ttl
        self._sessions: OrderedDict = OrderedDict()  # {token: {user_id, expires_at, ...}}
        self._lock = threading.RLock()

    def create(self, user_id: int, username: str, role: str = "user",
               ip: str = "", user_agent: str = "") -> str:
        """Buat session baru. Return token."""
        token = secrets.token_urlsafe(32)
        now = time.time()

        session = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "created_at": now,
            "expires_at": now + self.ttl,
            "ip": ip,
            "user_agent": user_agent[:200] if user_agent else "",
        }

        with self._lock:
            self._sessions[token] = session
            self._sessions.move_to_end(token)

            # Evict kalau kelebihan
            while len(self._sessions) > self.max_size:
                self._sessions.popitem(last=False)

        logger.info(f"🔐 Session created: {username} ({token[:8]}...)")
        return token

    def get(self, token: str) -> Optional[dict]:
        """Ambil session. Return None kalau tidak ada/expired."""
        if not token:
            return None

        with self._lock:
            session = self._sessions.get(token)
            if not session:
                return None

            # Cek expired
            if time.time() > session["expires_at"]:
                del self._sessions[token]
                return None

            # Refresh posisi (LRU)
            self._sessions.move_to_end(token)
            return session

    def delete(self, token: str) -> bool:
        """Hapus session."""
        with self._lock:
            if token in self._sessions:
                del self._sessions[token]
                return True
            return False

    def delete_user_sessions(self, user_id: int) -> int:
        """Hapus semua session milik user."""
        with self._lock:
            to_delete = [
                t for t, s in self._sessions.items()
                if s["user_id"] == user_id
            ]
            for t in to_delete:
                del self._sessions[t]
            return len(to_delete)

    def cleanup(self) -> int:
        """Hapus session yang expired."""
        now = time.time()
        with self._lock:
            expired = [
                t for t, s in self._sessions.items()
                if now > s["expires_at"]
            ]
            for t in expired:
                del self._sessions[t]
            return len(expired)

    def stats(self) -> dict:
        """Statistik."""
        with self._lock:
            return {
                "active_sessions": len(self._sessions),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl,
            }


# Singleton
session_store = SessionStore()


# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════
def create_session(user_id: int, username: str, role: str = "user",
                   ip: str = "", user_agent: str = "") -> str:
    return session_store.create(user_id, username, role, ip, user_agent)


def get_session(token: str) -> Optional[dict]:
    return session_store.get(token)


def delete_session(token: str) -> bool:
    return session_store.delete(token)


def cleanup_sessions() -> int:
    return session_store.cleanup()