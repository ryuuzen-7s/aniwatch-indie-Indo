# 🎌 AniWatch API

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/ryuuzen-7s/aniwatch-indie-Indo/blob/main/MD/CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Anicorporation.img-green.svg)](https://github.com/ryuuzen-7s/aniwatch-indie-Indo/blob/main/MD/LICENSE.md)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)]()

> **Update Terbaru (v1.4.0)**: Penambahan **Jadwal Harian**, optimasi **Pagination (max 10 item)**, **GZip Compression**, dan **Tool Edit Data Anime by ID** untuk mempermudah *maintenance*.

---

## ✨ Fitur Utama

- 🎬 **Scraper Multi-Source** — Otakudesu (aktif), Kuramanime, AnimeIndo.
- 🔒 **API Key Required** — Endpoint `/share/*` butuh API key (`X-API-Key`).
- 🚦 **Rate Limit** — Per API key, session, atau IP.
- ⚡ **Cache 2-Tier** — Memory + file (persistent).
- 🚫 **Method Restriction** — Hanya `GET` & `POST` (selain endpoint khusus).
- 🤖 **Auto Agent** — Scrape anime kosong di background.
- 📅 **Jadwal Harian** — Filter anime berdasarkan hari tayang.
- 🛡️ **Pagination & GZip** — Maksimal 10 item per halaman untuk menghemat memori client.
- 🛠️ **CLI Tools** — Manajemen database, API Key, dan edit data manual.

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

### 3. Jalankan Server (3 Mode)
Kamu bisa menjalankan semuanya sekaligus menggunakan satu klik:
```bash
start.bat
```
*(Akan membuka 3 terminal: API Server, ZROK Tunnel, dan Agent Scraper).*

Atau jalankan manual:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level warning
```

### 4. Akses Layanan
- **Portal**: `http://localhost:8000/portal`
- **Docs (Swagger)**: `http://localhost:8000/docs`
- **Monitoring**: `http://localhost:8000/monitor`

---

## 📡 API Endpoints (v1.4.0)

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

## 🛠️ CLI Tools (Manual)

Kamu bisa mengakses menu interaktif dengan menjalankan:
```bash
tools.bat
```

**Fitur Tools:**
- **[1] DB Monitor** — Cek isi database.
- **[2] Add Pass** — Buat/kelola API Key.
- **[3] Data Edit** — Edit data anime di database (Judul, Hari Tayang, dll) berdasarkan ID.
- **[4-7] Analyzer** — Analisa JSON slug & genre.
- **[10] Scraper Update** — Scrape anime on-going.
- **[17] Test Suite** — Jalankan pytest.

---

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (WAL mode) + SQLAlchemy
- **Validation**: Pydantic v2
- **HTTP Client**: requests + tenacity
- **HTML Parser**: BeautifulSoup + lxml
- **Compression**: GZipMiddleware

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