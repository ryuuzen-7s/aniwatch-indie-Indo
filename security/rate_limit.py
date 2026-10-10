"""
security/rate_limit.py — Rate limiter in-memory.
"""
import time
import logging
import threading
from typing import Optional, Dict, Tuple
from collections import deque
from dataclasses import dataclass


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
@dataclass
class LimitConfig:
    """Config untuk 1 limit."""
    max_requests: int
    window_seconds: int


# Default limit per tipe
LIMITS = {
    "anonymous": LimitConfig(max_requests=10, window_seconds=60),     # ← dari 30 → 10
    "api_key": LimitConfig(max_requests=100, window_seconds=60),      # default, override DB
    "session": LimitConfig(max_requests=60, window_seconds=60),
    "auth": LimitConfig(max_requests=5, window_seconds=300),
    "admin": LimitConfig(max_requests=1000, window_seconds=60),
}


# ═══════════════════════════════════════════════════════════
#  STORE
# ═══════════════════════════════════════════════════════════
class RateLimitStore:
    """
    Sliding window rate limiter.
    Menyimpan timestamp request per key.
    """

    def __init__(self):
        self._data: Dict[str, deque] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = 300  # cleanup tiap 5 menit
        self._last_cleanup = time.time()

    def check(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, dict]:
        """
        Cek apakah request masih dalam limit.
        Return: (allowed, info)
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            # Auto-cleanup kadang-kadang
            if now - self._last_cleanup > self._cleanup_interval:
                self._cleanup(cutoff=now - 3600)
                self._last_cleanup = now

            # Ambil queue
            if key not in self._data:
                self._data[key] = deque()

            q = self._data[key]

            # Buang yang expired
            while q and q[0] < cutoff:
                q.popleft()

            # Cek limit
            current = len(q)
            allowed = current < max_requests

            if allowed:
                q.append(now)

            # Info
            remaining = max(0, max_requests - len(q))
            reset_at = (q[0] + window_seconds) if q else (now + window_seconds)

            info = {
                "limit": max_requests,
                "remaining": remaining,
                "reset_at": int(reset_at),
                "reset_in": int(max(0, reset_at - now)),
                "window": window_seconds,
            }

            return allowed, info

    def _cleanup(self, cutoff: float):
        """Hapus key yang sudah tidak dipakai."""
        empty_keys = []
        for key, q in self._data.items():
            # Buang yang expired
            while q and q[0] < cutoff:
                q.popleft()
            # Kalau kosong, tandai hapus
            if not q:
                empty_keys.append(key)

        for key in empty_keys:
            del self._data[key]

        if empty_keys:
            logger.debug(f"Rate limit cleanup: {len(empty_keys)} keys dihapus")

    def reset(self, key: str) -> bool:
        """Reset 1 key."""
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def reset_all(self) -> int:
        """Reset semua."""
        with self._lock:
            count = len(self._data)
            self._data.clear()
            return count

    def stats(self) -> dict:
        """Statistik."""
        with self._lock:
            return {
                "active_keys": len(self._data),
                "total_requests_tracked": sum(len(q) for q in self._data.values()),
            }


# Singleton
rate_limit_store = RateLimitStore()


# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════
def check_rate_limit(
    key: str,
    limit_type: str = "anonymous",
    override_max: Optional[int] = None,
    override_window: Optional[int] = None,
) -> Tuple[bool, dict]:
    """
    Cek rate limit.

    Args:
        key             : identifier (IP, API key prefix, user_id)
        limit_type      : "anonymous" | "api_key" | "session" | "auth" | "admin"
        override_max    : override max_requests
        override_window : override window_seconds

    Returns:
        (allowed, info)
    """
    cfg = LIMITS.get(limit_type, LIMITS["anonymous"])
    max_req = override_max or cfg.max_requests
    window = override_window or cfg.window_seconds

    return rate_limit_store.check(key, max_req, window)


def reset_rate_limit(key: str) -> bool:
    """Reset limit untuk 1 key."""
    return rate_limit_store.reset(key)


def reset_all_rate_limits() -> int:
    """Reset semua."""
    return rate_limit_store.reset_all()


def rate_limit_stats() -> dict:
    """Statistik."""
    return rate_limit_store.stats()


# ═══════════════════════════════════════════════════════════
#  KEY BUILDERS
# ═══════════════════════════════════════════════════════════
def key_by_ip(ip: str, scope: str = "general") -> str:
    """Key berdasarkan IP."""
    return f"ip:{ip}:{scope}"


def key_by_api_key(key_prefix: str) -> str:
    """Key berdasarkan API key."""
    return f"apikey:{key_prefix}"


def key_by_user(user_id: int) -> str:
    """Key berdasarkan user ID."""
    return f"user:{user_id}"


def key_by_endpoint(ip: str, endpoint: str) -> str:
    """Key berdasarkan IP + endpoint (untuk endpoint sensitif)."""
    return f"ep:{endpoint}:{ip}"


# ═══════════════════════════════════════════════════════════
#  TEST
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import time

    print("=" * 60)
    print("  RATE LIMIT TEST")
    print("=" * 60)

    # Test 1: Under limit
    print("\n[Test 1] Limit 3 per 10 detik, request 5x")
    for i in range(1, 6):
        ok, info = check_rate_limit(
            key="test:user1",
            limit_type="anonymous",
            override_max=3,
            override_window=10,
        )
        status = "ALLOW" if ok else "BLOCK"
        print(f"  Request {i}: {status} | remaining={info['remaining']}")

    # Test 2: Setelah window
    print("\n[Test 2] Tunggu 11 detik, request lagi")
    print("  ... tunggu ...")
    time.sleep(11)
    ok, info = check_rate_limit(
        key="test:user1",
        limit_type="anonymous",
        override_max=3,
        override_window=10,
    )
    print(f"  Request: {'ALLOW' if ok else 'BLOCK'} | remaining={info['remaining']}")

    # Stats
    print("\nStats:", rate_limit_stats())