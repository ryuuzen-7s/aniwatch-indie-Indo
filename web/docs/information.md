# 🎌 AniWatch — Project Information

> **Status:** ✅ **Method Restrictor telah di-overwrite** — 2026-10-08
> **Version:** 1.0.1 (Method Restriction)
> **Base URL:** https://aniwatch.share.zrok.io
> **Docs:** `/docs` · **Monitor:** `/monitor` · **Portal:** `/portal`

---

## 📋 Ringkasan Project

| Aspek | Detail |
|-------|--------|
| **Nama** | AniWatch API |
| **Framework** | FastAPI + SQLAlchemy + Pydantic v2 |
| **DB** | SQLite (WAL mode) — `data/db/aniwatch.db` |
| **Auth** | API Key (`X-API-Key`) + Session Cookie + Bearer |
| **Cache** | 2-tier (memory + file) |
| **Rate Limit** | In-memory sliding window |
| **Method Restriction** | ✅ **GET & POST only** (renovasi terbaru) |
| **Source** | Otakudesu (scraper) |
| **Deployment** | Uvicorn + ZROK |

---

## 🚨 Status Overwrite — Method Restrictor

> **PENTING:** File-file berikut telah di-**overwrite** pada renovasi method restrictor (2026-10-08).
> Jangan gunakan versi lama dari file-file ini.

### ✅ File yang Sudah Di-overwrite

| # | File | Aksi | Baris |
|---|------|------|-------|
| 1 | `api/middleware/method_restrictor.py` | 🆕 **BUAT BARU** | ~107 |
| 2 | `api/middleware/__init__.py` | ✏️ Overwrite | +4 |
| 3 | `config.py` | ✏️ Overwrite (setting + 2 property) | +25 |
| 4 | `main.py` | ✏️ Overwrite (import + CORS + middleware) | +9 / -1 |
| 5 | `.env.example` | ✏️ Overwrite (section baru) | +8 |
| 6 | `test/test_api.py` | ✏️ Overwrite (tambah `TestMethodRestrictor`) | +75 |
| 7 | `.env` | ✏️ Update manual | +3 |

### ⚠️ File yang TIDAK Berubah

| Folder/File | Status |
|-------------|--------|
| `api/routes/*` | ✅ Tidak diubah |
| `api/models/*` | ✅ Tidak diubah |
| `api/services/*` | ✅ Tidak diubah |
| `api/exceptions.py` | ✅ Tidak diubah (dipakai) |
| `api/deps.py` | ✅ Tidak diubah |
| `web/*` | ✅ Tidak diubah |
| `db/*` | ✅ Tidak diubah |
| `security/*` | ✅ Tidak diubah |
| `core/*` | ✅ Tidak diubah |
| `cache/*` | ✅ Tidak diubah |
| `tools/*` | ✅ Tidak diubah |
| `agent/*` | ✅ Tidak diubah |
| `control/*` | ✅ Tidak diubah |
| `docs/*` | ✅ Tidak diubah |
| `test/*` (selain `test_api.py`) | ✅ Tidak diubah |

---

## 🎯 Aturan Method Restriction

### ✅ Method yang Diizinkan

| Method | Status | Keterangan |
|--------|--------|------------|
| `GET` | ✅ Allowed | Semua endpoint |
| `POST` | ✅ Allowed | Semua endpoint |
| `OPTIONS` | ✅ Allowed | CORS preflight (selalu lolos) |
| `HEAD` | ✅ Allowed | Health check (selalu lolos) |

### ❌ Method yang Diblokir

| Method | Status | Response |
|--------|--------|----------|
| `PUT` | ❌ Blocked | **405 Method Not Allowed** |
| `DELETE` | ❌ Blocked | **405** (kecuali `/keys/*`) |
| `PATCH` | ❌ Blocked | **405** |

### 🔓 Path yang Dikecualikan (Excluded)

Path berikut **dilewati** dari restriction (bisa akses method apapun):

| Path | Alasan |
|------|--------|
| `/keys/*` | Portal butuh `DELETE` untuk revoke API key |
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/openapi.json` | OpenAPI spec |
| `/monitor` | Custom monitoring dashboard |
| `/monitor/static` | Static assets dashboard |

---

## 📡 Daftar Endpoint

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
| POST | `/share/errorid/{slug}` | Report link error |
| POST | `/share/empty/{slug}` | Paksa scrape |
| POST | `/share/linkask/{slug}` | Cek link |

### 🔐 Auth

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/login` | Login user |
| POST | `/logout` | Logout |
| POST | `/register` | Register user |
| POST | `/get-key` | Generate API key |
| GET | `/me` | Info user |
| GET | `/keys` | List API key |
| DELETE | `/keys/{id}` | Revoke key |

### ⚡ Cache & Rate Limit

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/cache/stats` | Statistik cache |
| POST | `/cache/clear` | Hapus cache |
| POST | `/cache/invalidate/{slug}` | Invalidate cache |
| GET | `/rate-limit/stats` | Statistik rate limit |
| POST | `/rate-limit/reset` | Reset rate limit |

### 🖥️ Admin & Portal

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/admin/db-info` | Info DB (admin) |
| GET | `/monitor` | Monitoring dashboard |
| GET | `/portal` | Web portal |
| GET | `/portal/*.html` | HTML pages |

---

## 🧪 Verifikasi Cepat

```cmd
tools.bat verify
```

Atau manual:
```cmd
curl -s -o nul -w "GET  /health     : %{http_code}\n" http://localhost:8000/health
curl -s -o nul -w "PUT  /share/now  : %{http_code}\n" -X PUT http://localhost:8000/share/now
curl -s -o nul -w "DEL  /share/now  : %{http_code}\n" -X DELETE http://localhost:8000/share/now
curl -s -o nul -w "PATCH /share/now : %{http_code}\n" -X PATCH http://localhost:8000/share/now
curl -s -o nul -w "DEL  /keys/999   : %{http_code}\n" -X DELETE http://localhost:8000/keys/999
```

**Ekspektasi:**
```
GET  /health     : 200
PUT  /share/now  : 405  ← BLOCKED
DEL  /share/now  : 405  ← BLOCKED
PATCH /share/now : 405  ← BLOCKED
DEL  /keys/999   : 401/403/404  ← EXCLUDED
```

---

## 📊 Struktur Folder

```
aniwatch/
├── main.py                     Entry point
├── config.py                   Settings
├── logger.py                   Logging (legacy)
├── requirements.txt
├── start.bat                   Launcher server
├── tools.bat                   Menu tools
├── information.md              ← FILE INI
├── CHANGELOG.md                ← Changelog
├── note.md                     Command reference
│
├── api/                        API layer
│   ├── middleware/             ★ Method restrictor + rate limit
│   ├── models/                 Pydantic schemas
│   ├── routes/                 Endpoints
│   ├── services/               Business logic
│   ├── deps.py
│   └── exceptions.py
│
├── web/                        Portal (HTML + assets)
├── db/                         Database layer
├── security/                   Auth
├── cache/                      Cache
├── core/                       Scraper
├── agent/                      Agent scraper
├── control/                    DB control
├── tools/                      Utility tools
├── test/                       Test suite
├── docs/                       Monitoring HTML
├── data/                       DB + cache + log
├── backup/                     Arsip
└── bin/                        Script temporary
```

---

## 🛠️ Tools Reference

Semua tools ada di folder `tools\`. Jalankan dari root:

```cmd
python tools\<nama>.py
```

Atau pakai `tools.bat` untuk menu interaktif.

| Command | Fungsi |
|---------|--------|
| `tools.bat` | Menu interaktif |
| `tools.bat db` | Monitor DB |
| `tools.bat key` | Manage API key |
| `tools.bat test` | Test suite |
| `tools.bat verify` | Verifikasi 405 |
| `tools.bat scanapi` | Scan folder api |
| `tools.bat update` | Scrape ongoing |

Lihat `note.md` untuk command lengkap.

---

## 🔧 Konfigurasi `.env`

### Method Restriction

```env
ALLOWED_METHODS=GET,POST
METHOD_EXCLUDED_PATHS=/keys,/docs,/redoc,/openapi.json,/monitor
```

### Server

```env
HOST=0.0.0.0
PORT=8000
WORKERS=1
```

### Database

```env
DB_PATH=data/db/aniwatch.db
DB_ECHO=false
```

### Cache

```env
CACHE_ENABLED=true
CACHE_MEMORY_SIZE=1000
CACHE_TTL_ANIME=604800
```

---

## 🚀 Cara Menjalankan

### 1. Local Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Atau:
```cmd
start.bat
```

### 2. ZROK Tunnel

```bash
zrok share reserved aniwatch
```

### 3. Buka di Browser

- Portal: http://localhost:8000/portal
- Docs: http://localhost:8000/docs
- Monitor: http://localhost:8000/monitor

---

## ⚠️ Catatan Penting

1. **Method restrictor aktif** — `PUT`/`DELETE`/`PATCH` akan 405 (kecuali `/keys/*`).
2. **`OPTIONS` & `HEAD` selalu lolos** — untuk CORS preflight & health check.
3. **Format error konsisten** — `{success, data, meta, error}`.
4. **File `bin/_fix_*.py`** adalah script fix lama — jangan dijalankan sembarangan.
5. **File `backup/*.bak`** adalah arsip — jangan edit.

---

## 📞 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| CMD nutup saat test | Pakai `tools.bat test` (fixed) |
| Folder `test/` hilang | Pindahkan kembali dari `tools/test/` |
| 405 di endpoint yang seharusnya jalan | Cek `METHOD_EXCLUDED_PATHS` di `.env` |
| CORS preflight gagal | `OPTIONS` harus lolos (cek middleware) |
| DELETE `/keys/{id}` gagal | Path `/keys` harus di-exclude |

---

**Terakhir diupdate:** 2026-10-08
**Author:** AniWatch Project
**License:** Private