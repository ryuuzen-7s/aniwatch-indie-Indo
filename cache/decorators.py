"""
cache/decorators.py — Decorator untuk auto-cache fungsi.
"""
import functools
import hashlib
import json
import logging
from typing import Callable, Optional

from .strategy import get_cached, set_cached


logger = logging.getLogger(__name__)


def _make_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """Bikin key dari fungsi + args."""
    try:
        payload = json.dumps(
            {"args": args, "kwargs": kwargs},
            sort_keys=True,
            default=str,
        )
    except (TypeError, ValueError):
        payload = str(args) + str(kwargs)

    h = hashlib.md5(payload.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{h}"


def cached(
    prefix: str,
    ttl: int = 300,
    file_persist: bool = False,
    skip_if: Callable = None,
):
    """
    Decorator untuk cache hasil fungsi.

    Usage:
        @cached("my_func", ttl=60)
        def my_func(x, y):
            return x + y
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = _make_key(prefix, args, kwargs)

            # Cek cache
            cached_val = get_cached(key)
            if cached_val is not None:
                logger.debug(f"@{prefix}: cache HIT")
                return cached_val

            # Jalankan fungsi
            result = func(*args, **kwargs)

            # Skip cache kalau hasil kosong / error
            if skip_if and skip_if(result):
                return result

            # Simpan ke cache
            if result is not None:
                set_cached(key, result, ttl=ttl, file_persist=file_persist)

            return result

        # Expose function asli
        wrapper.__wrapped__ = func
        wrapper.cache_prefix = prefix
        return wrapper

    return decorator