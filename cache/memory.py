"""
cache/memory.py — In-memory cache dengan TTL.
Thread-safe, LRU-style (FIFO dengan max size).
"""
import time
import logging
import threading
from typing import Any, Optional
from collections import OrderedDict


logger = logging.getLogger(__name__)


class MemoryCache:
    """
    Thread-safe in-memory cache dengan TTL.

    Contoh:
        mc = MemoryCache(max_size=500)
        mc.set("key", {"data": 1}, ttl=60)
        val = mc.get("key")  # → {"data": 1}
    """

    def __init__(self, max_size: int = 500):
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()  # {key: (value, expires_at)}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    # ═══════════════════════════════════════════════════════
    #  CORE
    # ═══════════════════════════════════════════════════════
    def get(self, key: str) -> Optional[Any]:
        """Ambil nilai. Return None kalau tidak ada/expired."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, expires_at = self._cache[key]

            # Cek expired
            if expires_at and time.time() > expires_at:
                del self._cache[key]
                self._misses += 1
                return None

            # Refresh posisi (LRU)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Simpan nilai dengan TTL (detik). None = tanpa expiry."""
        expires_at = time.time() + ttl if ttl else None

        with self._lock:
            # Kalau sudah ada, hapus dulu (biar posisi di akhir)
            if key in self._cache:
                del self._cache[key]

            self._cache[key] = (value, expires_at)

            # Evict kalau kelebihan
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)  # FIFO: hapus yang paling lama

    def delete(self, key: str) -> bool:
        """Hapus key."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Hapus semua."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def invalidate_prefix(self, prefix: str) -> int:
        """Hapus semua key dengan prefix tertentu."""
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._cache[k]
            return len(keys_to_delete)

    # ═══════════════════════════════════════════════════════
    #  STATS
    # ═══════════════════════════════════════════════════════
    def stats(self) -> dict:
        """Statistik cache."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total else 0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 2),
            }

    def cleanup_expired(self) -> int:
        """Hapus semua yang expired. Return jumlah yang dihapus."""
        now = time.time()
        with self._lock:
            expired = [
                k for k, (_, exp) in self._cache.items()
                if exp and now > exp
            ]
            for k in expired:
                del self._cache[k]
            return len(expired)


# ═══════════════════════════════════════════════════════════
#  SINGLETON
# ═══════════════════════════════════════════════════════════
from config import settings

memory_cache = MemoryCache(max_size=settings.cache_memory_size)