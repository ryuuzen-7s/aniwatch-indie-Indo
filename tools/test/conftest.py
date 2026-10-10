"""Pytest fixtures."""
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
