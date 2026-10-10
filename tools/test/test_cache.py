"""Test cache layer."""
import time
import pytest

from cache.strategy import (
    get_cached, set_cached, invalidate,
    cache_anime, get_anime_cached, invalidate_anime,
)


def test_set_get():
    set_cached("test:t1", {"val": 1}, ttl=10)
    assert get_cached("test:t1") == {"val": 1}


def test_expiry():
    set_cached("test:t2", "exp", ttl=1)
    assert get_cached("test:t2") == "exp"
    time.sleep(2)
    assert get_cached("test:t2") is None


def test_invalidate():
    set_cached("test:t3", "x", ttl=10)
    assert get_cached("test:t3") == "x"
    invalidate("test:t3")
    assert get_cached("test:t3") is None


def test_anime_cache():
    cache_anime("test-slug", "otakudesu", {"title": "Test"})
    assert get_anime_cached("test-slug", "otakudesu") == {"title": "Test"}
    invalidate_anime("test-slug", "otakudesu")
    assert get_anime_cached("test-slug", "otakudesu") is None
