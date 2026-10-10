"""
cache/strategy.py — Orchestrator cache.

Alur: memory → file → (kosong, caller harus fetch dari DB/sumber)
"""
import logging
from typing import Any, Optional

from config import settings
from .memory import memory_cache
from .file_cache import file_cache


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  CORE GET/SET
# ═══════════════════════════════════════════════════════════
def get_cached(key: str) -> Optional[Any]:
    """
    Ambil dari memory dulu, lalu file.
    Return None kalau tidak ada di dua-duanya.
    """
    if not settings.cache_enabled:
        return None

    # 1. Memory
    val = memory_cache.get(key)
    if val is not None:
        logger.debug(f"Cache HIT (memory): {key}")
        return val

    # 2. File
    val = file_cache.get(key)
    if val is not None:
        logger.debug(f"Cache HIT (file): {key}")
        # Promote ke memory
        memory_cache.set(key, val, ttl=300)
        return val

    logger.debug(f"Cache MISS: {key}")
    return None


def set_cached(key: str, value: Any, ttl: Optional[int] = None,
               file_persist: bool = False) -> None:
    """
    Simpan ke memory & file.
    - ttl: TTL untuk memory
    - file_persist: kalau True, simpan juga ke file (TTL file = ttl * 10)
    """
    if not settings.cache_enabled:
        return

    memory_cache.set(key, value, ttl=ttl)

    if file_persist and ttl:
        # File cache pakai TTL lebih lama
        file_cache.set(key, value, ttl=ttl * 10)


def invalidate(key_or_prefix: str, prefix: bool = False) -> int:
    """Hapus dari cache (memory + file)."""
    count = 0

    if prefix:
        count += memory_cache.invalidate_prefix(key_or_prefix)
        # File cache tidak support prefix, kita skip (atau hapus semua)
    else:
        if memory_cache.delete(key_or_prefix):
            count += 1
        if file_cache.delete(key_or_prefix):
            count += 1

    return count


def clear_all() -> dict:
    """Bersihkan semua cache."""
    memory_cache.clear()
    file_count = file_cache.clear()
    return {"memory": "cleared", "file": file_count}


# ═══════════════════════════════════════════════════════════
#  KEY BUILDERS
# ═══════════════════════════════════════════════════════════
def _key_anime(slug: str, source: str) -> str:
    return f"anime:{source}:{slug}"


def _key_episode_list(slug: str, source: str) -> str:
    return f"episodes:{source}:{slug}"


def _key_episode_detail(slug: str, number: int, source: str) -> str:
    return f"episode:{source}:{slug}:{number}"


def _key_poster(slug: str, source: str) -> str:
    return f"poster:{source}:{slug}"


def _key_search(query: str) -> str:
    return f"search:{query.lower()}"


def _key_season(season: str) -> str:
    return f"season:{season.lower()}"


def _key_now() -> str:
    return "now:ongoing"


def _key_stats() -> str:
    return "system:stats"


# ═══════════════════════════════════════════════════════════
#  HIGH-LEVEL HELPERS
# ═══════════════════════════════════════════════════════════
def cache_anime(slug: str, source: str, data: dict) -> None:
    """Cache data anime."""
    set_cached(
        _key_anime(slug, source),
        data,
        ttl=settings.cache_ttl_anime,
        file_persist=True,
    )


def get_anime_cached(slug: str, source: str) -> Optional[dict]:
    """Ambil anime dari cache."""
    return get_cached(_key_anime(slug, source))


def cache_episode(slug: str, number: int, source: str, data: dict) -> None:
    """Cache detail episode."""
    set_cached(
        _key_episode_detail(slug, number, source),
        data,
        ttl=settings.cache_ttl_episode_detail,
        file_persist=True,
    )


def get_episode_cached(slug: str, number: int, source: str) -> Optional[dict]:
    """Ambil episode detail dari cache."""
    return get_cached(_key_episode_detail(slug, number, source))


def cache_list(key_type: str, key_id: str, data: list, ttl: int = None) -> None:
    """Cache list (episode list, search results, dll)."""
    set_cached(
        f"{key_type}:{key_id}",
        data,
        ttl=ttl or settings.cache_ttl_episode_list,
        file_persist=False,  # List tidak perlu persist ke file
    )


def invalidate_anime(slug: str, source: str = "otakudesu") -> int:
    """Hapus semua cache terkait 1 anime."""
    count = 0
    count += invalidate(_key_anime(slug, source), prefix=False)
    count += invalidate(f"episodes:{source}:{slug}")
    count += invalidate(f"poster:{source}:{slug}")
    count += invalidate(f"episode:{source}:{slug}:", prefix=True)
    return count


# ═══════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════
def cache_stats() -> dict:
    """Statistik cache (memory + file)."""
    return {
        "enabled": settings.cache_enabled,
        "memory": memory_cache.stats(),
        "file": file_cache.stats(),
    }


# ═══════════════════════════════════════════════════════════
#  TEST
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import time

    print("=" * 60)
    print("  CACHE TEST")
    print("=" * 60)

    # Test set/get
    set_cached("test:key1", {"foo": "bar"}, ttl=5)
    print(f"get('test:key1')  : {get_cached('test:key1')}")

    # Test expiry
    set_cached("test:key2", "expires soon", ttl=1)
    print(f"get('test:key2')  : {get_cached('test:key2')}")
    print("  ... tunggu 2 detik ...")
    time.sleep(2)
    print(f"get('test:key2')  : {get_cached('test:key2')} (expired)")

    # Test file cache
    set_cached("test:key3", {"persist": True}, ttl=60, file_persist=True)
    memory_cache.delete("test:key3")
    print(f"get('test:key3')  : {get_cached('test:key3')} (from file)")

    # Test invalidation
    invalidate_anime("test-anime", "otakudesu")
    print(f"Invalidate anime  : OK")

    # Stats
    print()
    print("Stats:", cache_stats())