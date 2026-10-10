"""
Abstract base class untuk semua agent scraper Aniwatch.
"""
import time
import random
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import config
from logger import get_logger


class BaseScraper(ABC):
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or config.BASE_URL).rstrip("/")
        self.log = get_logger(self.__class__.__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })

    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        url = self._absolute_url(url)
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                self.log.debug(f"GET {url} (attempt {attempt})")
                resp = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
                resp.raise_for_status()
                time.sleep(config.REQUEST_DELAY + random.uniform(0, 0.5))
                return BeautifulSoup(resp.text, "lxml")
            except requests.RequestException as e:
                wait = config.RETRY_BACKOFF ** attempt
                self.log.warning(
                    f"Gagal GET {url} (attempt {attempt}/{config.MAX_RETRIES}): {e}. "
                    f"Tunggu {wait:.1f}s..."
                )
                time.sleep(wait)
        self.log.error(f"Semua retry gagal untuk: {url}")
        return None

    @abstractmethod
    def get_anime(self, slug_or_url: str) -> dict: ...

    @abstractmethod
    def get_episode(self, slug_or_url: str) -> dict: ...

    def _absolute_url(self, url: str) -> str:
        if url.startswith("http"):
            return url
        return urljoin(self.base_url + "/", url.lstrip("/"))

    @staticmethod
    def slug_from_url(url: str) -> str:
        path = urlparse(url).path.rstrip("/")
        return path.split("/")[-1] if path else ""

    @staticmethod
    def domain_from_url(url: str) -> str:
        return urlparse(url).netloc