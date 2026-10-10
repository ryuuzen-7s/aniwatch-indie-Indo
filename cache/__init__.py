"""cache — Cache layer untuk AniWatch."""
from .memory import MemoryCache, memory_cache
from .file_cache import FileCache, file_cache
from .strategy import (
    get_cached, set_cached, invalidate,
    cache_anime, cache_episode, cache_list,
)
from .decorators import cached

__all__ = [
    "MemoryCache", "memory_cache",
    "FileCache", "file_cache",
    "get_cached", "set_cached", "invalidate",
    "cache_anime", "cache_episode", "cache_list",
    "cached",
]