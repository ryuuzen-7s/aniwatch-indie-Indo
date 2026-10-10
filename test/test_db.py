"""Test database models & repository."""
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
