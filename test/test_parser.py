"""Test HTML parser."""
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
