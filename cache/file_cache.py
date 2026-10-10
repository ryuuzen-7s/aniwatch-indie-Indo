"""
cache/file_cache.py — File-based cache (JSON di disk).
Persisten antar restart.
"""
import json
import time
import hashlib
import logging
import threading
from pathlib import Path
from typing import Any, Optional


logger = logging.getLogger(__name__)


CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class FileCache:
    """
    Cache berbasis file JSON.
    Key → hash → filename.
    """

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _key_to_path(self, key: str) -> Path:
        """Hash key jadi nama file yang aman."""
        h = hashlib.md5(key.encode("utf-8")).hexdigest()[:16]
        return self.cache_dir / f"{h}.json"

    def get(self, key: str) -> Optional[Any]:
        """Ambil nilai. Return None kalau tidak ada/expired/error."""
        path = self._key_to_path(key)

        with self._lock:
            if not path.exists():
                return None

            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                # File rusak, hapus
                try:
                    path.unlink()
                except OSError:
                    pass
                return None

        # Cek expired
        expires_at = data.get("_expires_at")
        if expires_at and time.time() > expires_at:
            try:
                path.unlink()
            except OSError:
                pass
            return None

        return data.get("value")

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Simpan nilai dengan TTL."""
        path = self._key_to_path(key)
        expires_at = time.time() + ttl if ttl else None

        payload = {
            "_key": key,
            "_created_at": time.time(),
            "_expires_at": expires_at,
            "value": value,
        }

        with self._lock:
            try:
                path.write_text(
                    json.dumps(payload, ensure_ascii=False, default=str),
                    encoding="utf-8",
                )
            except (OSError, TypeError) as e:
                logger.warning(f"File cache write error: {e}")

    def delete(self, key: str) -> bool:
        """Hapus key."""
        path = self._key_to_path(key)
        with self._lock:
            if path.exists():
                try:
                    path.unlink()
                    return True
                except OSError:
                    return False
            return False

    def clear(self) -> int:
        """Hapus semua cache file."""
        with self._lock:
            count = 0
            for f in self.cache_dir.glob("*.json"):
                try:
                    f.unlink()
                    count += 1
                except OSError:
                    pass
            return count

    def cleanup_expired(self) -> int:
        """Hapus file yang expired."""
        now = time.time()
        count = 0

        with self._lock:
            for f in self.cache_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    exp = data.get("_expires_at")
                    if exp and now > exp:
                        f.unlink()
                        count += 1
                except Exception:
                    # Rusak? hapus
                    try:
                        f.unlink()
                        count += 1
                    except OSError:
                        pass

        return count

    def stats(self) -> dict:
        """Statistik."""
        files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files if f.exists())
        return {
            "files": len(files),
            "total_bytes": total_size,
            "total_kb": round(total_size / 1024, 2),
            "dir": str(self.cache_dir),
        }


# Singleton
file_cache = FileCache()