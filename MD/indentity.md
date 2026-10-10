# 🎌 AniWatch — Identity

> **Official Identity Document**
> **Project:** AniWatch API
> **Organization:** Anicorporation.img
> **Developer:** Anikuze Ryuuzen
> **Version:** 1.0.1
> **Year:** ©2026

---

## 📌 Project Overview

**AniWatch** adalah REST API untuk scraping anime dari berbagai sumber (Otakudesu, Kuramanime, AnimeIndo). Dibangun dengan **FastAPI** + **SQLAlchemy** + **Pydantic v2** dengan arsitektur modern.

### 🎯 Tujuan

- Menyediakan API bersih untuk data anime (metadata, episode, stream, download)
- Mendukung multiple source (multi-mirror)
- Cache 2-tier (memory + file) untuk performa
- Rate limiting untuk mencegah abuse
- Method restriction (GET & POST only) untuk keamanan

### 🌐 Base URL

| Environment | URL |
|-------------|-----|
| **Local** | `http://localhost:8000` |
| **Public (ZROK)** | `https://aniwatch.share.zrok.io` |

### 📚 Dokumentasi

| Endpoint | Fungsi |
|----------|--------|
| `/docs` | Swagger UI (interactive) |
| `/redoc` | ReDoc (read-only) |
| `/monitor` | Custom monitoring dashboard |
| `/portal` | Web portal (user panel) |

---

## 📡 Daftar Endpoint

### 🌐 System

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/` | Landing page (info API) |
| `GET` | `/health` | Health check (uptime) |
| `GET` | `/stats` | Statistik database & sistem |

### 🎬 Share — Data Anime

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/share/anime/{slug}` | Detail anime by slug |
| `GET` | `/share/episodeid/{slug}` | List semua episode dari anime |
| `GET` | `/share/episode/{number}/{slug}` | Detail episode (stream + download) |
| `GET` | `/share/posterid/{slug}` | URL poster anime |
| `GET` | `/share/query?q={keyword}` | Cari anime (hybrid: DB + live scrape) |
| `GET` | `/share/season/{season}` | Anime per season (fall-2026, dll) |
| `GET` | `/share/now` | Anime ongoing terbaru |
| `POST` | `/share/errorid/{slug}` | Report link error |
| `POST` | `/share/empty/{slug}` | Paksa scrape anime |
| `POST` | `/share/linkask/{slug}` | Cek ketersediaan link |

### 🔐 Auth

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/login` | Login user |
| `POST` | `/logout` | Logout user |
| `POST` | `/register` | Register user baru |
| `POST` | `/get-key` | Generate API key |
| `GET` | `/me` | Info user sekarang |
| `GET` | `/keys` | List API key user |
| `DELETE` | `/keys/{key_id}` | Revoke API key |

### ⚡ Cache

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/cache/stats` | Statistik cache (memory + file) |
| `POST` | `/cache/clear` | Hapus semua cache |
| `POST` | `/cache/invalidate/{slug}` | Invalidate cache 1 anime |

### 🚦 Rate Limit

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/rate-limit/stats` | Statistik rate limit |
| `POST` | `/rate-limit/reset` | Reset rate limit (admin) |

### 🖥️ Admin & Portal

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/admin/db-info` | Info DB detail (admin) |
| `GET` | `/monitor` | Custom monitoring dashboard |
| `GET` | `/portal` | Web portal utama |
| `GET` | `/portal/login.html` | Halaman login |
| `GET` | `/portal/dashboard.html` | Dashboard user |
| `GET` | `/portal/detail.html` | Detail API key |

### ⚠️ Method Restriction

**Sejak v1.0.1**, API hanya menerima **`GET`** dan **`POST`**.

| Method | Status | Keterangan |
|--------|--------|------------|
| `GET` | ✅ Allowed | Semua endpoint |
| `POST` | ✅ Allowed | Semua endpoint |
| `OPTIONS` | ✅ Allowed | CORS preflight |
| `HEAD` | ✅ Allowed | Health check |
| `PUT` | ❌ 405 | Method Not Allowed |
| `DELETE` | ❌ 405 | Kecuali `/keys/*` |
| `PATCH` | ❌ 405 | Method Not Allowed |

**Path dikecualikan:** `/keys`, `/docs`, `/redoc`, `/openapi.json`, `/monitor`

---

## 🎯 Fitur Utama

### 1. Scraper Multi-Source

- **Otakudesu** (aktif)
- Kuramanime (planned)
- AnimeIndo (planned)

### 2. Cache 2-Tier

- **Memory** — Cepat, ephemeral (LRU + TTL)
- **File** — Persisten antar restart (JSON di disk)

### 3. Rate Limiter

- In-memory sliding window
- Configurable per tipe: anonymous, api_key, session, auth, admin
- Headers standar: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### 4. Autentikasi

- **API Key** via header `X-API-Key`
- **Session Cookie** untuk browser
- **Bearer Token** via header `Authorization`

### 5. Agent Auto-Scraper

- Internal scheduler (APScheduler)
- Windows Task Scheduler integration
- Config via `agent/.env`

### 6. Web Portal

- Request API key (quick key)
- Login/register
- Manage keys (create, revoke)
- Detail view

---

## 🏢 Organization

| Aspek | Detail |
|-------|--------|
| **Nama** | Anicorporation.img |
| **Developer** | Anikuze Ryuuzen |
| **Tahun** | ©2026 |
| **Negara** | Indonesia |
| **Status** | Private Project |

### Tim Inti

| Nama | Peran |
|------|-------|
| **Anikuze Ryuuzen** | Lead Developer |
| **Tia Yunia** | Anggota |
| **Lio Syberion** | Pendiri Organisasi |
| **Yuna Syres** | Anggota (Organisasi Lama) |
| **WinterHouse** | Anggota (Organisasi Lama) |
| **Syres Alona** | Pendiri Organisasi Lama |

---

## 📜 Sejarah Organisasi

| Periode | Organisasi | Pendiri |
|---------|-----------|---------|
| Sebelum 2026 | **SyberEco.corp.ind** | Syres Alona |
| 2026 — Sekarang | **Anicorporation.img** | Lio Syberion |

**Serah terima:** 2026 — dari SyberEco.corp.ind ke Anicorporation.img

Detail lengkap di `copyright.md`.

---

## 🛠️ Tech Stack

| Layer | Teknologi |
|-------|-----------|
| **Framework** | FastAPI |
| **Server** | Uvicorn |
| **Database** | SQLite (WAL mode) + SQLAlchemy |
| **Validation** | Pydantic v2 |
| **HTTP Client** | requests + tenacity |
| **HTML Parser** | BeautifulSoup + lxml |
| **Scheduler** | APScheduler |
| **Tunnel** | ZROK |

---

## 📊 Statistik

| Komponen | Jumlah |
|----------|--------|
| **Endpoint** | 25+ |
| **Model DB** | 6 |
| **Middleware** | 2 |
| **Service** | 7 |
| **Router** | 11 |
| **Tools** | 15 |
| **Test** | 45+ |

---

## 📞 Kontak

| Kanal | Info |
|-------|------|
| **Developer** | Anikuze Ryuuzen |
| **Organisasi** | Anicorporation.img |
| **Public API** | https://aniwatch.share.zrok.io |
| **Docs** | https://aniwatch.share.zrok.io/docs |

---

## 📄 Lisensi

AniWatch dilisensikan di bawah **Anicorporation.img License ©2026**.

Lihat `LICENSE.md` dan `copyright.md` untuk detail.

---

**©2026 Anicorporation.img — All Rights Reserved**
**Developer:** Anikuze Ryuuzen