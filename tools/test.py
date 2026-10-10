"""
_gen_test.py - Generate semua file test di folder test/.
Jalankan: python _gen_test.py
"""
from pathlib import Path

ROOT = Path(__file__).parent
TEST_DIR = ROOT / "test"
TEST_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  FILE YANG AKAN DIBUAT
# ═══════════════════════════════════════════════════════════
FILES = {

    # ─── __init__.py ───
    "test/__init__.py": '''"""test - Test suite AniWatch."""
''',

    # ─── conftest.py ───
    "test/conftest.py": '''"""Pytest fixtures."""
import sys
import pytest
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))


@pytest.fixture
def sample_anime_data():
    return {
        "source": "otakudesu",
        "slug": "test-anime-fixture",
        "url": "https://example.com/anime/test/",
        "metadata": {
            "title": "Test Anime Fixture",
            "studio": "Test Studio",
            "genres": ["Action", "Adventure"],
            "total_episode": 12,
        },
        "episode_details": [{
            "url": "https://example.com/episode/1/",
            "title": "Test Episode 1",
            "episode_number": 1,
            "streams": [{"host": "test.net", "url": "https://test.net/stream"}],
            "downloads": [
                {"quality": "720p", "host": "Mega", "url": "https://mega.nz/test", "alive": True},
            ],
        }],
    }


@pytest.fixture
def client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)
''',

    # ─── test_db.py ───
    "test/test_db.py": '''"""Test database models & repository."""
import pytest
from sqlalchemy import select, func

from pathlib import Path
import sys
# ═══════════════════════════════════════════════════════════
#  PATH FIX — supaya bisa import dari root project
# ═══════════════════════════════════════════════════════════
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# ═══════════════════════════════════════════════════════════

from db import get_session, init_db
from db.models import Anime, Episode, DownloadLink
from db.repository import (
    AnimeRepository, EpisodeRepository,
    DownloadRepository, save_scrape_result,
)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def test_create_anime():
    with get_session() as s:
        anime = AnimeRepository.upsert(s, {
            "source": "otakudesu",
            "slug": "test-create",
            "title": "Test Create",
            "genres": ["Action"],
        })
        assert anime.id is not None
        assert anime.slug == "test-create"


def test_upsert_anime():
    with get_session() as s:
        a1 = AnimeRepository.upsert(s, {
            "source": "otakudesu", "slug": "test-upsert", "title": "V1"
        })
        a2 = AnimeRepository.upsert(s, {
            "source": "otakudesu", "slug": "test-upsert", "title": "V2"
        })
        assert a1.id == a2.id
        assert a2.title == "V2"

    with get_session() as s:
        count = s.scalar(
            select(func.count()).select_from(Anime)
            .where(Anime.slug == "test-upsert")
        )
        assert count == 1


def test_json_field():
    with get_session() as s:
        AnimeRepository.upsert(s, {
            "source": "otakudesu",
            "slug": "test-json",
            "title": "Test",
            "genres": ["Action", "Comedy"],
            "info": {"key": "value"},
        })

    with get_session() as s:
        anime = AnimeRepository.get_by_slug(s, "test-json")
        assert anime.genres == ["Action", "Comedy"]
        assert anime.info == {"key": "value"}


def test_save_scrape_result(sample_anime_data):
    counters = save_scrape_result(sample_anime_data)
    assert counters["anime"] == 1
    assert counters["episodes"] == 1
    assert counters["downloads"] == 1


def test_download_unique_constraint():
    with get_session() as s:
        anime = AnimeRepository.upsert(s, {
            "source": "otakudesu", "slug": "test-uq", "title": "T"
        })
        ep = EpisodeRepository.upsert(s, {
            "anime_id": anime.id, "slug": "test-uq-ep1",
            "url": "", "title": "Ep1", "episode_number": 1,
        })
        d1 = DownloadRepository.upsert(s, {
            "episode_id": ep.id, "quality": "720p", "host": "Mega", "url": "url1",
        })
        d2 = DownloadRepository.upsert(s, {
            "episode_id": ep.id, "quality": "720p", "host": "Mega", "url": "url2",
        })
        assert d1.id == d2.id
        assert d2.url == "url2"
''',

    # ─── test_parser.py ───
    "test/test_parser.py": '''"""Test HTML parser."""
import pytest
from pathlib import Path
from bs4 import BeautifulSoup

from core.sources.otakudesu import OtakudesuParser


@pytest.fixture
def sample_html():
    paths = [
        Path("debug_output/phase1_debug.html"),
        Path("test/fixtures/sample_anime.html"),
    ]
    for p in paths:
        if p.exists():
            return p.read_text(encoding="utf-8")
    pytest.skip("Tidak ada sample HTML")


@pytest.fixture
def parser():
    return OtakudesuParser(base_url="https://otakudesu.blog")


def test_extract_metadata(sample_html, parser):
    soup = BeautifulSoup(sample_html, "lxml")
    meta = parser.extract_metadata(soup)
    assert meta["title"] is not None
    assert len(meta["genres"]) > 0


def test_extract_episodes(sample_html, parser):
    soup = BeautifulSoup(sample_html, "lxml")
    eps = parser.extract_episodes(soup)
    assert len(eps) >= 1
''',

    # ─── test_api.py ───
    "test/test_api.py": '''"""Test API endpoints."""
import pytest


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_stats(client):
    r = client.get("/stats")
    assert r.status_code == 200
    assert "counts" in r.json()["data"]


def test_404_format(client):
    r = client.get("/tidak-ada-endpoint")
    assert r.status_code == 404
    data = r.json()
    assert data["success"] is False
    assert data["error"] is not None
''',

    # ─── test_security.py ───
    "test/test_security.py": '''"""Test auth & rate limit."""
import time
import pytest


def test_register_success(client):
    username = f"testuser_{int(time.time()*1000)}"
    r = client.post("/register", json={
        "username": username,
        "password": "test123456",
        "email": "test@test.com",
    })
    assert r.status_code == 201
    assert r.json()["data"]["username"] == username


def test_register_short_password(client):
    r = client.post("/register", json={
        "username": "shortpw",
        "password": "12",
    })
    assert r.status_code == 422


def test_login_success(client):
    username = f"loginuser_{int(time.time()*1000)}"
    client.post("/register", json={
        "username": username,
        "password": "test123456",
    })
    r = client.post("/login", json={
        "username": username,
        "password": "test123456",
    })
    assert r.status_code == 200
    assert "token" in r.json()["data"]


def test_login_wrong_password(client):
    r = client.post("/login", json={
        "username": "nonexistent_user_xyz",
        "password": "wrong",
    })
    assert r.status_code == 401


def test_get_api_key(client):
    r = client.post("/get-key", json={
        "name": "test-key",
        "rate_limit": 100,
    })
    assert r.status_code == 200
    assert r.json()["data"]["key"].startswith("anw_")


def test_me_anonymous(client):
    r = client.get("/me")
    assert r.status_code == 200
    assert r.json()["data"]["authenticated"] is False


def test_me_with_api_key(client):
    r = client.post("/get-key", json={"name": "test-key-2"})
    api_key = r.json()["data"]["key"]
    r = client.get("/me", headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert r.json()["data"]["authenticated"] is True
    assert r.json()["data"]["method"] == "api_key"


def test_rate_limit_headers(client):
    r = client.get("/share/now")
    assert "X-RateLimit-Limit" in r.headers
    assert "X-RateLimit-Remaining" in r.headers
''',

    # ─── test_cache.py ───
    "test/test_cache.py": '''"""Test cache layer."""
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
''',

    # ─── test_fetcher.py ───
    "test/test_fetcher.py": '''"""Test fetcher."""
import pytest

from core.fetcher import is_blocked, MIN_VALID_HTML_SIZE


def test_is_blocked_empty():
    assert is_blocked("") is True


def test_is_blocked_short():
    assert is_blocked("<html></html>") is True


def test_is_blocked_server_busy():
    html = "<html><body>Server is busy</body></html>" + "x" * 3000
    assert is_blocked(html) is True


def test_is_blocked_cloudflare():
    html = "<html><body>Just a moment...</body></html>" + "x" * 3000
    assert is_blocked(html) is True


def test_not_blocked():
    html = "<!DOCTYPE html><html><body>" + "x" * 5000 + "</body></html>"
    assert is_blocked(html) is False
''',

    # ─── fixtures/sample_anime.json ───
    "test/fixtures/sample_anime.json": '''{
  "source": "otakudesu",
  "slug": "sample-anime",
  "url": "https://otakudesu.blog/anime/sample-anime/",
  "metadata": {
    "title": "Sample Anime",
    "title_jp": "サンプルアニメ",
    "studio": "Sample Studio",
    "genres": ["Action", "Comedy"],
    "total_episode": 12
  },
  "episode_details": [
    {
      "url": "https://otakudesu.blog/episode/sample-ep-1/",
      "title": "Sample Episode 1",
      "episode_number": 1,
      "streams": [{"host": "desustream.net", "url": "https://desustream.net/embed/xxx"}],
      "downloads": [
        {"quality": "720p", "host": "Mega", "url": "https://mega.nz/xxx", "alive": true},
        {"quality": "480p", "host": "Acefile", "url": "https://acefile.co/xxx", "alive": true}
      ]
    }
  ]
}
''',

    # ─── fixtures/.gitkeep ───
    "test/fixtures/.gitkeep": "",
}


# ═══════════════════════════════════════════════════════════
#  TULIS SEMUA FILE
# ═══════════════════════════════════════════════════════════
print("=" * 60)
print("  GENERATE TEST FILES")
print("=" * 60)

ok = 0
fail = 0

for rel_path, content in FILES.items():
    target = ROOT / rel_path
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        lines = content.count(chr(10)) + 1
        size = target.stat().st_size
        print(f"OK   {rel_path:<40} ({lines:>3} lines, {size:>6} bytes)")
        ok += 1
    except Exception as e:
        print(f"FAIL {rel_path}: {e}")
        fail += 1


# ═══════════════════════════════════════════════════════════
#  CEK PYTEST INSTALLED
# ═══════════════════════════════════════════════════════════
print()
print("=" * 60)
print("  CEK PYTEST")
print("=" * 60)

try:
    import pytest
    print(f"OK   pytest {pytest.__version__}")
except ImportError:
    print("FAIL pytest tidak terinstall")
    print("     Install: pip install pytest")

# Cek httpx (dibutuhkan TestClient)
try:
    import httpx
    print(f"OK   httpx {httpx.__version__}")
except ImportError:
    print("FAIL httpx tidak terinstall")
    print("     Install: pip install httpx")


print()
print("=" * 60)
print(f"  SELESAI: {ok} OK, {fail} FAIL")
print("=" * 60)
print()
print("Jalankan test:")
print("  pytest test/ -v")
print()