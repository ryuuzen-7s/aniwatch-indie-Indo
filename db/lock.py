"""
db/lock.py — Global write lock untuk SQLite.

Mencegah 2 proses/proses tulis DB bersamaan.
SQLite hanya support 1 writer pada 1 waktu.
"""
import threading
import logging


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  GLOBAL WRITE LOCK
# ═══════════════════════════════════════════════════════════
# Semua operasi write harus acquire lock ini dulu.
# RLock → reentrant, aman untuk nested call.
WRITE_LOCK = threading.RLock()


class WriteLockContext:
    """
    Context manager untuk write lock.

    Usage:
        with WriteLockContext():
            # ... operasi write ...
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.acquired = False

    def __enter__(self):
        self.acquired = WRITE_LOCK.acquire(timeout=self.timeout)
        if not self.acquired:
            logger.error(f"[WriteLock] Gagal acquire lock dalam {self.timeout}s")
            raise TimeoutError(
                f"Tidak bisa acquire write lock dalam {self.timeout}s"
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            WRITE_LOCK.release()
        return False


# ═══════════════════════════════════════════════════════════
#  HELPER
# ═══════════════════════════════════════════════════════════
def is_locked() -> bool:
    """Cek apakah write lock sedang dipegang."""
    acquired = WRITE_LOCK.acquire(blocking=False)
    if acquired:
        WRITE_LOCK.release()
        return False
    return True