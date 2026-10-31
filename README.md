# 🎌 AniWatch API

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/ryuuzen-7s/aniwatch-indie-Indo/blob/main/MD/CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Anicorporation.img-green.svg)](https://github.com/ryuuzen-7s/aniwatch-indie-Indo/blob/main/MD/LICENSE.md)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)]()

> **Update Terbaru (v1.3.0)**: Pemisahan Endpoint Jadwal Harian (`/share/day/{hari}`) dan optimalisasi memori dengan GZip Compression & Pagination (max 10 data). [Baca Changelog Lengkap](https://github.com/ryuuzen-7s/aniwatch-indie-Indo/blob/main/MD/CHANGELOG.md).

---

## ✨ Fitur Utama

- 🎬 **Scraper Multi-Source** — Otakudesu (aktif), Kuramanime, AnimeIndo.
- 🔒 **API Key Required** — Endpoint `/share/*` butuh API key (`X-API-Key`).
- 🚦 **Rate Limit** — Per API key, session, atau IP.
- ⚡ **Cache 2-Tier** — Memory + file (persistent).
- 🚫 **Method Restriction** — Hanya `GET` & `POST`.
- 🤖 **Auto Agent** — Scrape anime kosong di background.
- 📅 **Jadwal Harian** — Filter anime berdasarkan hari tayang.
- 🛡️ **Pagination** — Maksimal 10 item per halaman untuk optimasi client.

---

## 🚀 Menjalankan Server

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup `.env`
```bash
copy .env.example .env
```

### 3. Jalankan Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level warning
```

### 4. Buka Dokumentasi
- **Portal**: `http://localhost:8000/portal`
- **Docs (Swagger)**: `http://localhost:8000/docs`
- **Monitoring**: `http://localhost:8000/monitor`

---

## 📡 API Endpoints (v1.3.0)

### 🔓 Publik (Tanpa API Key)
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/health` | Health check |
| POST | `/login` | Login user |
| POST | `/register` | Register user |
| POST | `/get-key` | Generate API key |

### 🔒 Terproteksi (Butuh API Key)
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/share/anime/{slug}` | Detail anime |
| GET | `/share/episodeid/{slug}` | List episode (Paginated) |
| GET | `/share/query?q=` | Search anime |
| GET | `/share/now` | Anime update terbaru (Paginated) |
| **GET** | **`/share/day/{hari}`** | **Jadwal anime harian (Paginated)** |
| GET | `/share/season/{season}` | Anime per season (Paginated) |

---

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (WAL mode) + SQLAlchemy
- **Validation**: Pydantic v2
- **HTTP Client**: requests + tenacity
- **HTML Parser**: BeautifulSoup + lxml

---

## 📄 License

**Anicorporation.img License v1.0** — ©2026. 
Lihat [`MD/LICENSE.md`](MD/LICENSE.md) untuk detail.

---

## 👥 Kontak

- **Organisasi**: Anicorporation.img
- **Developer**: [Anikuze Ryuuzen](https://github.com/ryuuzen-7s)
- **Founder**: Lio Syberion

---
**©2026 Anicorporation.img — All Rights Reserved**