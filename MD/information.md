# 🎌 AniWatch — Project Information

> **Version:** 1.5.0
> **Base URL:** https://aniwatch.share.zrok.io
> **Docs:** `/docs` · **Monitor:** `/monitor` · **Portal:** `/portal`

---

## 📋 Ringkasan Project
| Aspek | Detail |
|-------|--------|
| **Framework** | FastAPI + SQLAlchemy + Pydantic v2 |
| **DB** | SQLite (WAL mode) — `data/db/aniwatch.db` |
| **Auth** | API Key (`X-API-Key`) + Session Cookie + Bearer |
| **Rate Limit** | In-memory sliding window |
| **Source** | Otakudesu (scraper) |
| **Deployment** | Uvicorn + ZROK |

---

## 🎯 Aturan Method Restriction
**Sejak v1.0.1**, API hanya menerima **`GET`** dan **`POST`**. 
*`PUT`, `DELETE`, `PATCH` akan diblokir dengan 405 Method Not Allowed (kecuali untuk path yang dikecualikan).*

### 🔓 Path yang Dikecualikan
| Path | Alasan |
|------|--------|
| `/keys/*` | Portal butuh `DELETE` untuk revoke API key |
| `/docs`, `/redoc`, `/openapi.json` | Dokumentasi |
| `/monitor` | Dashboard |

---

## 📡 Daftar Endpoint (v1.5.0)

### 🌐 System
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/` | Landing page |
| GET | `/health` | Health check |
| GET | `/stats` | Statistik DB |

### 🎬 Share (Data Anime)
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/share/anime/{slug}` | Detail anime |
| GET | `/share/episodeid/{slug}` | List episode |
| GET | `/share/episode/{number}/{slug}` | Detail episode |
| GET | `/share/posterid/{slug}` | URL poster |
| GET | `/share/query?q=` | Cari anime |
| GET | `/share/season/{season}` | Anime per season |
| GET | `/share/now` | Anime ongoing terbaru |
| **GET** | **`/share/day/{hari}`** | **Jadwal harian (BARU v1.3.0)** |
| POST | `/share/errorid/{slug}` | Report link error |
| POST | `/share/empty/{slug}` | Paksa scrape |
| POST | `/share/linkask/{slug}` | Cek link |

### 🔐 Auth
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/login`, `/logout`, `/register` | Manajemen user |
| POST | `/get-key` | Generate API key |
| GET | `/me` | Info user |
| GET, DELETE | `/keys`, `/keys/{id}` | List & Revoke API key |

### ⚡ Cache & Rate Limit
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET, POST | `/cache/stats`, `/cache/clear` | Manajemen cache |
| GET, POST | `/rate-limit/stats`, `/rate-limit/reset` | Manajemen rate limit |

---

## 🚀 Cara Menjalankan
1. Local Server: `uvicorn main:app --host 0.0.0.0 --port 8000` (atau `start.bat`)
2. ZROK Tunnel: `zrok share reserved aniwatch`
3. Buka di Browser: `http://localhost:8000/portal`

---

**Terakhir diupdate:** 2026-11-02
**Author:** AniWatch Project
