"""
core/sources/base.py — Base class untuk semua source parser.
Setiap source harus implement method di sini.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

from bs4 import BeautifulSoup


class BaseParser(ABC):
    """
    Abstract parser. Setiap source implement ini.
    """

    # Nama source (harus sama dengan key di .env, lowercase)
    name: str = "base"

    # Pattern URL untuk deteksi tipe halaman
    url_patterns: Dict[str, str] = {
        # "anime":   r"/anime/([^/]+)/?$",
        # "episode": r"/episode/([^/]+)/?$",
    }

    def __init__(self, base_url: str = ""):
        self.base_url = base_url.rstrip("/")

    # ═══════════════════════════════════════════════════════
    #  WAJIB DIIMPLEMENTASI
    # ═══════════════════════════════════════════════════════
    @abstractmethod
    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Ambil metadata anime dari halaman /anime/{slug}."""
        ...

    @abstractmethod
    def extract_episodes(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Ambil daftar episode dari halaman /anime/{slug}."""
        ...

    @abstractmethod
    def extract_stream(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Ambil link streaming dari halaman /episode/{slug}."""
        ...

    @abstractmethod
    def extract_downloads(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Ambil link download dari halaman /episode/{slug}."""
        ...

    # ═══════════════════════════════════════════════════════
    #  UTIL (bisa dipakai semua source)
    # ═══════════════════════════════════════════════════════
    def slug_from_url(self, url: str) -> str:
        """Ambil slug dari URL. Override kalau format beda."""
        return url.rstrip("/").split("/")[-1]

    def normalize_url(self, url: str) -> str:
        """Ubah URL relatif jadi absolut."""
        if not url:
            return ""
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.base_url + url
        return f"{self.base_url}/{url}"

    def clean_text(self, text: Optional[str]) -> str:
        """Bersihkan teks dari whitespace berlebih."""
        if not text:
            return ""
        return " ".join(text.split()).strip()

    def find_text(self, parent, selector: str, default: str = "") -> str:
        """Ambil teks dari selector, return default kalau tidak ada."""
        if not parent:
            return default
        el = parent.select_one(selector)
        return self.clean_text(el.get_text()) if el else default