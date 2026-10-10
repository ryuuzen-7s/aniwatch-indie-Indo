"""
Scraper Otakudesu — berbasis analisis HTML nyata.
"""
import re
from typing import Optional

from config import config
from logger import get_logger
from agent.base import BaseScraper   # ⬅️ DIUBAH


class OtakudesuScraper(BaseScraper):
    """Scraper untuk otakudesu.blog."""

    def __init__(self, base_url: Optional[str] = None):
        super().__init__(base_url or "https://otakudesu.blog")
        self.log = get_logger("OtakudesuScraper")

    # ------------------------------------------------------------------
    def get_anime(self, slug_or_url: str) -> dict:
        url = self._normalize_anime_url(slug_or_url)
        self.log.info(f"Mengambil detail anime: {url}")
        soup = self.fetch(url)
        if not soup:
            return {"error": "fetch_failed", "url": url}
        try:
            data = {
                "url": url,
                "slug": self.slug_from_url(url),
                "title": self._get_title(soup),
                "image": self._get_image(soup),
                "info": self._get_info(soup),
                "synopsis": self._get_synopsis(soup),
                "episodes": self._get_episodes(soup),
                "batch_available": self._has_batch(soup),
            }
            self.log.info(f"OK: {data['title']} — {len(data['episodes'])} episode")
            return data
        except Exception as e:
            self.log.exception(f"Gagal parsing {url}: {e}")
            return {"error": str(e), "url": url}

    def get_episode(self, slug_or_url: str) -> dict:
        url = self._normalize_episode_url(slug_or_url)
        self.log.info(f"Mengambil episode: {url}")
        soup = self.fetch(url)
        if not soup:
            return {"error": "fetch_failed", "url": url}
        try:
            data = {
                "url": url,
                "slug": self.slug_from_url(url),
                "title": self._get_title(soup),
                "streams": self._get_streams(soup),
                "downloads": self._get_downloads(soup),
                "prev": self._get_nav(soup, "prev"),
                "next": self._get_nav(soup, "next"),
            }
            self.log.info(f"OK: {data['title']}")
            return data
        except Exception as e:
            self.log.exception(f"Gagal parsing episode {url}: {e}")
            return {"error": str(e), "url": url}

    # ------------------------------------------------------------------
    def _normalize_anime_url(self, slug_or_url: str) -> str:
        if slug_or_url.startswith("http"):
            return slug_or_url
        return f"{self.base_url}/anime/{slug_or_url.strip('/')}/"

    def _normalize_episode_url(self, slug_or_url: str) -> str:
        if slug_or_url.startswith("http"):
            return slug_or_url
        return f"{self.base_url}/episode/{slug_or_url.strip('/')}/"

    # ------------------------------------------------------------------
    def _get_title(self, soup) -> str:
        tag = soup.select_one("div.jdlrx h1")
        if not tag:
            t = soup.title.get_text(strip=True) if soup.title else ""
            return re.sub(r"\s*\|\s*Otaku Desu\s*$", "", t)
        for span in tag.select("span"):
            span.decompose()
        return tag.get_text(strip=True)

    def _get_image(self, soup) -> dict:
        img = soup.select_one("div.fotoanime img")
        if not img:
            return {}
        return {
            "src": img.get("src", ""),
            "srcset": img.get("srcset", ""),
            "alt": img.get("alt", ""),
        }

    def _get_synopsis(self, soup) -> str:
        tag = soup.select_one("div.sinopc")
        return tag.get_text(" ", strip=True) if tag else ""

    def _get_info(self, soup) -> dict:
        info = {}
        container = soup.select_one("div.infozingle")
        if not container:
            return info
        for p in container.select("p"):
            text = p.get_text(" ", strip=True)
            if ":" not in text:
                continue
            key, _, value = text.partition(":")
            key = key.strip().lower()
            value = value.strip()
            if key == "genre":
                info["genre"] = [a.get_text(strip=True) for a in p.select("a")]
            else:
                info[key] = value
        return info

    def _get_episodes(self, soup) -> list[dict]:
        episodes = []
        seen = set()
        for li in soup.select("div.episodelist ul li"):
            a = li.select_one("a[href*='/episode/']")
            if not a:
                continue
            href = self._absolute_url(a["href"])
            if href in seen:
                continue
            seen.add(href)
            date_tag = li.select_one("span.zeebr")
            date = date_tag.get_text(strip=True) if date_tag else ""
            episodes.append({
                "title": a.get_text(strip=True),
                "url": href,
                "slug": self.slug_from_url(href),
                "date": date,
            })
        episodes.sort(key=self._episode_number)
        return episodes

    def _has_batch(self, soup) -> bool:
        for block in soup.select("div.episodelist"):
            ul = block.select_one("ul")
            if ul and ul.select("li a[href*='/batch/']"):
                return True
        return False

    @staticmethod
    def _episode_number(ep: dict) -> int:
        m = re.search(r"episode-(\d+)", ep.get("slug", ""))
        return int(m.group(1)) if m else 0

    # ------------------------------------------------------------------
    def _get_streams(self, soup) -> list[dict]:
        streams, seen = [], set()
        for iframe in soup.select("iframe"):
            src = iframe.get("src", "")
            if src and src not in seen:
                seen.add(src)
                streams.append({
                    "provider": self._provider_from_url(src),
                    "url": src,
                })
        for a in soup.select("div.mirrorstream a, .mirrorstream a"):
            href = a.get("href", "")
            if href and href not in seen:
                seen.add(href)
                streams.append({
                    "provider": a.get_text(strip=True) or "mirror",
                    "url": href,
                })
        return streams

    def _get_downloads(self, soup) -> list[dict]:
        downloads = []
        for a in soup.select("div.download a, .download a"):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            if href and text and href.startswith("http"):
                downloads.append({"label": text, "url": href})
        return downloads

    def _get_nav(self, soup, direction: str) -> Optional[dict]:
        a = soup.select_one(f"a.{direction}, .flir a.{direction}")
        if not a or not a.get("href"):
            return None
        return {
            "title": a.get_text(strip=True),
            "url": self._absolute_url(a["href"]),
        }

    @staticmethod
    def _provider_from_url(url: str) -> str:
        m = re.search(r"//([^/]+)/", url)
        return m.group(1) if m else "unknown"