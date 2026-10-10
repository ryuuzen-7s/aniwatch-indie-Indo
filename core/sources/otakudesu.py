"""
core/sources/otakudesu.py — Parser untuk Otakudesu.
Berdasarkan hasil debug: 
- Metadata: .infozingle p (dengan <strong>label</strong>)
- Sinopsis: .sinopc
- Poster: .fotoanime img
- Episode list: .episodelist a
- Stream: iframe
- Download: .download a (grouped by quality)
"""
import re
from typing import List, Dict, Any
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

from .base import BaseParser


class OtakudesuParser(BaseParser):
    name = "otakudesu"

    # ═══════════════════════════════════════════════════════
    #  METADATA
    # ═══════════════════════════════════════════════════════
    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        meta: Dict[str, Any] = {
            "title": None,
            "title_jp": None,
            "synopsis": None,
            "poster": None,
            "info": {},
            "genres": [],
            "rating": None,
        }

        # Judul
        h1 = soup.find("h1")
        if h1:
            meta["title"] = self.clean_text(h1.get_text())

        # Info dari .infozingle p → <p><strong>Label:</strong> value</p>
        for p in soup.select(".infozingle p"):
            strong = p.find(["strong", "b"])
            if strong:
                key = self.clean_text(strong.get_text()).rstrip(":").strip()
                val = self.clean_text(p.get_text())
                # Hapus label dari value
                val = val.replace(strong.get_text(), "", 1).strip(" :")
                if key and val:
                    meta["info"][key] = val

        # Ekstrak field spesifik dari info
        info = meta["info"]
        meta["title_jp"] = info.get("Japanese", "")
        meta["studio"] = info.get("Studio", "")
        meta["producer"] = info.get("Produser", "")
        meta["type"] = info.get("Tipe", "")
        meta["status"] = info.get("Status", "")
        meta["duration"] = info.get("Durasi", "")
        meta["release_date"] = info.get("Tanggal Rilis", "")

        # Total episode (parse int)
        total_ep = info.get("Total Episode", "")
        if total_ep:
            m = re.search(r"(\d+)", total_ep)
            meta["total_episode"] = int(m.group(1)) if m else None
        else:
            meta["total_episode"] = None

        # Sinopsis
        sinop = soup.select_one(".sinopc")
        if sinop:
            meta["synopsis"] = self.clean_text(sinop.get_text())

        # Poster
        poster = soup.select_one(".fotoanime img")
        if poster:
            meta["poster"] = poster.get("src", "")

        # Genre
        genres = []
        for a in soup.select('a[href*="/genres/"]'):
            g = self.clean_text(a.get_text())
            if g and g not in genres:
                genres.append(g)
        meta["genres"] = genres

        # Rating (kadang ada di span/div)
        for text in soup.stripped_strings:
            m = re.match(r"^([\d.]+)\s*/\s*10$", text.strip())
            if m:
                meta["rating"] = float(m.group(1))
                break

        return meta

    # ═══════════════════════════════════════════════════════
    #  EPISODE LIST
    # ═══════════════════════════════════════════════════════
    def extract_episodes(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        episodes = []
        seen = set()

        for a in soup.select('.episodelist a[href*="/episode/"], a[href*="/episode/"]'):
            href = a.get("href", "")
            if not href:
                continue

            url = self.normalize_url(href)
            if url in seen:
                continue
            seen.add(url)

            title = self.clean_text(a.get_text())
            if "batch" in title.lower() or "/batch/" in url.lower():
                continue

            # Coba ekstrak nomor episode dari judul
            ep_num = None
            m = re.search(r"episode\s*(\d+)", title, re.I)
            if m:
                ep_num = int(m.group(1))

            episodes.append({
                "title": title,
                "url": url,
                "slug": self.slug_from_url(url),
                "episode_number": ep_num,
            })

        # Urutkan berdasarkan nomor episode (ascending)
        episodes.sort(key=lambda e: (
            e["episode_number"] is None,
            e["episode_number"] or 0,
        ))

        return episodes

    # ═══════════════════════════════════════════════════════
    #  STREAM
    # ═══════════════════════════════════════════════════════
    def extract_stream(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        streams = []

        # iframe biasa
        for iframe in soup.find_all("iframe", src=True):
            src = iframe.get("src", "")
            if src.startswith("http"):
                streams.append({
                    "host": urlparse(src).netloc,
                    "url": src,
                    "quality": "default",
                })

        # #pembed (player embed)
        pembed = soup.select_one("#pembed")
        if pembed:
            iframe = pembed.find("iframe", src=True)
            if iframe and iframe.get("src", "").startswith("http"):
                src = iframe["src"]
                if not any(s["url"] == src for s in streams):
                    streams.append({
                        "host": urlparse(src).netloc,
                        "url": src,
                        "quality": "embed",
                    })

        return streams

    # ═══════════════════════════════════════════════════════
    #  DOWNLOAD
    # ═══════════════════════════════════════════════════════
    def extract_downloads(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        downloads = []
        container = soup.select_one(".download")
        if not container:
            return downloads

        current_quality = "unknown"

        # Iterasi semua elemen dalam .download
        for el in container.find_all(["h4", "h5", "strong", "b", "a"]):
            if el.name in ("h4", "h5", "strong", "b"):
                text = self.clean_text(el.get_text())
                # Deteksi kualitas (720p, MKV 480p, Mp4 1080p, dll)
                if re.search(r"\b\d{3,4}p\b|\bMKV\b|\bMP4\b", text, re.I):
                    current_quality = text

            elif el.name == "a" and el.get("href"):
                href = el["href"]
                # Filter: hanya link shortener desustream
                if "desustream" in href or "link." in href:
                    downloads.append({
                        "quality": current_quality,
                        "host": self.clean_text(el.get_text()),
                        "url": href,
                        "alive": True,  # default, nanti di-cek oleh analyzer
                    })

        return downloads