# 📝 Changelog — AniWatch API

Semua perubahan penting pada project AniWatch didokumentasikan di file ini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/),
versi mengikuti [Semantic Versioning](https://semver.org/).

---
## [1.1.1] — 2026-10-12 — Task Scheduler Update

### 🔧 Changed

- **`agent/install_task.bat`** — Interval 6 → **12 jam** (hemat CPU)
  - Tambah info command (query/run/uninstall)
- **`agent/cron_daily.bat`** — Tambah **log redirect** + **exit code**
  - Log ke `agent/logs/task_YYYYMMDD.log`
  - Auto-create folder log
- **`agent/cron-hourly.bat`** — Tambah log redirect
- **`agent/uninstall_task.bat`** — Rename dari `uinstall_task.bat`
  - Fix typo
  - Header lebih jelas

### 📊 Behavior

- Task jalan tiap **12 jam** (2x sehari)
- Log file per tanggal di `agent/logs/`
- Exit code di-track Task Scheduler
- Manual trigger via `schtasks /Run /TN "AniWatchAgent"`

---

## [1.1.0] — 2026-10-11 — Search → Agent → Response Flow (Planned)

### 🎯 Planned — Search Flow v2

Revisi logika search agar **client tahu apa yang terjadi** saat data kosong.

#### 🔄 Alur Baru

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ GET /share/query?q=naruto
     ↓
┌──────────────────────────────────────────┐
│  API: /share/query                       │
│                                          │
│  1. Cek DB (search_db)                   │
│     ↓                                    │
│  2. Ada? ── Ya ──→ Return 200 JSON       │
│     │                                    │
│     Tidak                                │
│     ↓                                    │
│  3. Live scrape Otakudesu                │
│     ↓                                    │
│  4. Dapat slug?                          │
│     ↓                                    │
│  5. Trigger Agent Worker (background)    │
│     ↓                                    │
│  6. Return 404 + agent info              │
│     (poll_url, retry_after)              │
└──────────────────────────────────────────┘
     ↓
┌──────────────────────────────────────────┐
│  Agent Worker (background thread)        │
│  1. scrape_anime(slug)                   │
│  2. save_scrape_result()                 │
│  3. Update status: "done"                │
└──────────────────────────────────────────┘
     ↓
┌──────────────────────────────────────────┐
│  Client Polling                          │
│  GET /share/scrape-status/{slug}         │
│                                          │
│  running → tunggu 3s                     │
│  done    → fetch ulang /share/query      │
│  error   → tampilkan error               │
└──────────────────────────────────────────┘
```

### 🆕 Added — Response Enhancement

#### `poll_url` di Response 404

```json
{
  "success": false,
  "error": {
    "code": "SEARCH_EMPTY",
    "message": "Tidak ada hasil untuk 'naruto'",
    "status": 404,
    "details": {
      "query": "naruto",
      "source": "otakudesu",
      "suggestion": "Data sedang di-scrape otomatis. Coba lagi dalam 30 detik.",
      "agent": {
        "triggered": true,
        "slug": "naruto-sub-indo",
        "status": "queued",
        "message": "Scrape 'naruto-sub-indo' dimulai di background",
        "poll_url": "/share/scrape-status/naruto-sub-indo",
        "retry_after": 30
      },
      "duration_ms": 3803
    }
  }
}
```

#### Query Parameter Baru: `?wait=true`

Client bisa **tunggu scraping selesai** sebelum response:

```http
GET /share/query?q=naruto&wait=true
```

**Behavior:**
- Kalau data kosong → trigger agent
- **Tunggu max 60 detik** sampai scraping selesai
- Re-search DB setelah selesai
- Return 200 dengan hasil, ATAU 404 kalau timeout

### 🔧 Changed

- **`api/routes/search.py`** — `search_endpoint()`:
  - Fallback slug dari query (kalau live search gagal)
  - Response 404 include `poll_url` + `retry_after`
  - Support parameter `?wait=true`
- **`api/services/search_service.py`**:
  - Tambah `wait_for_scrape(timeout=60)` — tunggu sampai tidak ada scrape running
  - Tambah `is_scrape_running()` — cek status global
- **`web/error/empty.html`**:
  - Auto-polling `/share/scrape-status/{slug}` tiap 3s
  - Auto-redirect ke `/portal/index.html?q={query}` setelah selesai
- **`web/assets/api.js`**:
  - Handle `poll_url` dari error response
  - Handle `?wait=true` flow

### 📊 Behavior Baru

| Skenario | Sebelum | Sesudah |
|----------|---------|---------|
| **Query kosong** | 404 tanpa info | 404 + `poll_url` + `retry_after` |
| **Client tunggu** | Manual polling | `?wait=true` auto tunggu |
| **Slug fallback** | ❌ Tidak ada | ✅ Dari query |
| **Notifikasi selesai** | ❌ Tidak ada | ✅ Polling + auto-redirect |
| **UX** | Bingung | Jelas |

### 🎯 Endpoint Baru

| Method | Endpoint | Fungsi |
|--------|----------|--------|
| `GET` | `/share/query?q=...&wait=true` | Tunggu scraping selesai |
| `GET` | `/share/scrape-status/{slug}` | Sudah ada (v1.0.5) |
| `GET` | `/share/scrape-jobs` | Sudah ada (v1.0.5) |

### 📋 Files Changed

| File | Aksi |
|------|------|
| `api/routes/search.py` | ✏️ Update |
| `api/services/search_service.py` | ✏️ Update |
| `web/error/empty.html` | ✏️ Update |
| `web/assets/api.js` | ✏️ Update |

---

## [1.0.8] — 2026-10-11 — Search Service Rewrite

### 🔧 Rewrite — `api/services/search_service.py`

- Tulis ulang total untuk fix ImportError & parser yang lebih baik
- **Tambah:** `is_scrape_running()`, `wait_for_scrape()`, `get_running_slugs()`
- **Tambah:** `clear_scrape_jobs()`, `cleanup_done_jobs()`
- **Fix:** Parser `search_live()` — handle `<h2><a>` + extract parent slug dari episode
- **Fix:** `trigger_agent_worker()` — retry DB lock + global lock
- **Improve:** `list_scrape_jobs()` — tambah counter done & error

### 🐛 Fixed

- **ImportError:** `cannot import name 'wait_for_scrape'` — sudah fix
- **Parser search_live:** Sebelum 0 hasil, sekarang return hasil
- **DB lock:** Retry 3x di agent worker

## [1.0.7] — 2026-10-10 — Database Lock Fix & DB Layer Rewrite

### 🐛 Fixed — Database Lock

- **Masalah:** `database is locked` saat force scrape + agent worker barengan
- **Penyebab:** 2 writer SQLite akses DB simultan (force_scrape + agent worker)
- **Fix:**
  - **Global write lock** — hanya 1 writer boleh jalan sekaligus
  - **Retry decorator** — auto retry 5x dengan exponential backoff
  - **Busy timeout 60s** — dari 30s
  - **Session close sebelum scrape** — hindari session aktif 30-40s
  - **WAL autocheckpoint** — cegah file `.db-wal` membesar

### 📦 Rewrite — DB Layer

#### 🆕 `db/lock.py` (BARU)

- `WRITE_LOCK` — global `threading.RLock`
- `WriteLockContext` — context manager
- `is_locked()` — helper

#### ✏️ `db/database.py`

- Timeout 30s → **60s**
- Tambah PRAGMA: `wal_autocheckpoint=1000`, `temp_store=MEMORY`
- Fungsi baru: `checkpoint_wal()`, `vacuum_db()`

#### ✏️ `db/models.py`

- Tambah field `max_requests` di `ApiKey`

#### ✏️ `db/repository.py`

- `@with_retry` decorator — 5x exponential backoff
- `save_scrape_result()` pakai `WriteLockContext`

#### ✏️ `db/__init__.py`

- Export lengkap + `lock.py`

### 📊 Behavior Baru

| Skenario | Sebelum | Sesudah |
|----------|---------|---------|
| **2 scrape bareng** | ❌ Locked | ✅ Retry, eventual success |
| **Busy timeout** | 30s | **60s** |
| **WAL autocheckpoint** | ❌ | ✅ 1000 pages |
| **Retry on locked** | ❌ | ✅ 5x |

---

## [1.0.6] — 2026-10-10 — API Key Required for Anime Data

### 🔒 Security — Wajib API Key

- **Endpoint `/share/*` WAJIB API key** (`X-API-Key` header)
- Tanpa API key → **401 Unauthorized**
- Endpoint publik (`/`, `/health`, `/stats`, `/docs`) tetap bisa diakses

### 📊 Rate Limit Baru

| Tipe | Max | Window |
|------|-----|--------|
| Anonymous | 10 | 60s |
| API Key | DB value | 60s |
| Session | 60 | 60s |
| Auth | 5 | 300s |
| Admin | 1000 | 60s |

### 🎯 Endpoint Terproteksi

- `GET /share/anime/{slug}`
- `GET /share/episodeid/{slug}`
- `GET /share/episode/{number}/{slug}`
- `GET /share/posterid/{slug}`
- `GET /share/query?q=`
- `GET /share/season/{season}`
- `GET /share/now`
- `POST /share/errorid/{slug}`
- `POST /share/empty/{slug}`
- `POST /share/linkask/{slug}`

### 🌐 Endpoint Publik

- `GET /`, `/health`, `/stats`
- `POST /login`, `/register`, `/get-key`
- `GET /docs`, `/redoc`, `/openapi.json`
- `GET /monitor`, `/portal/*`, `/md/*`

---

## [1.0.5] — 2026-10-10 — Backend Agent Trigger (Query Empty)

### 🎯 Added — Backend Agent Trigger

- **404 + Agent Trigger** di `/share/query` saat hasil kosong
- Spawn background thread
- Return 404 dengan detail agent

### 🌐 Endpoint Baru

| Method | Endpoint | Fungsi |
|--------|----------|--------|
| `GET` | `/share/scrape-status/{slug}` | Cek status scrape job |
| `GET` | `/share/scrape-jobs` | List semua scrape job |

### 🐛 Fixed

- **`search_live()`** parser Otakudesu:
  - Sebelum: Selector `.chivsrc li` (tidak match)
  - Sesudah: Cari `<h2><a>`, terima `/episode/` juga
- **Fallback slug** — dari query

---

## [1.0.4] — 2026-10-10 — Error Handling Pages

### 🎯 Added — Error Pages

- **`web/error/index.html`** — Query error
- **`web/error/empty.html`** — Empty result + trigger agent

### 🌐 URL Baru

| URL | Fungsi |
|-----|--------|
| `/error` | Query error page |
| `/error/empty.html` | Empty result page |

---

## [1.0.3] — 2026-10-10 — MD Folder Web Access

### 📚 Added — MD Folder Web Access

- Folder `MD/` bisa diakses via web
- `MD/index.html` — listing page
- Route `/md/` + `/md/{file}`

### 🌐 URL Baru

| URL | Fungsi |
|-----|--------|
| `/md/` | Listing file MD |
| `/md/usage.md` | File usage |
| `/md/CHANGELOG.md` | File changelog |
| `/md/identity.md` | File identity |
| `/md/LICENSE.md` | File license |
| `/md/copyright.md` | File copyright |
| `/md/information.md` | File info |
| `/md/note.md` | File note |

---

## [1.0.2] — 2026-10-09 — Documentation & CORS Fix

### 📚 Added — Documentation

- `usage.md`, `identity.md`, `LICENSE.md`, `copyright.md`, `information.md`, `note.md`

### 🔧 Fixed — CORS Preflight

- `OPTIONS /health` → 400 → **200 OK**
- Tambah `allow_origin_regex` untuk IP lokal

### 🔧 Changed — Middleware Order

- CORS didaftarkan paling akhir (paling luar)

---

## [1.0.1] — 2026-10-08 — Method Restriction

### 🎯 Added — Middleware Method Restrictor

- File baru: `api/middleware/method_restrictor.py`
- Hanya `GET` & `POST`
- `PUT`/`DELETE`/`PATCH` → 405
- Exclude: `/keys`, `/docs`, `/redoc`, `/openapi.json`, `/monitor`

### ✅ Tests

- 13 test baru di `test/test_api.py`

---

## [1.0.0] — 2026-10-06 — Initial Release

### 🎉 Added — Fitur Utama

- FastAPI + SQLAlchemy + Pydantic v2
- SQLite dengan WAL mode
- Scraper Otakudesu
- Cache 2-tier
- Rate limiter
- Auth: API Key + Session + Bearer
- Web portal + Monitoring dashboard
- Swagger UI + ReDoc

### 🎯 Endpoints

- `/share/*`, `/auth/*`, `/system/*`, `/cache/*`, `/rate-limit/*`, `/admin/*`

### 🛠️ Tools (15 files)

- `db_monitor.py`, `add_pass.py`, `scanner.py`, `scraper_update.py`, `scraper_by_genre.py`, `analyzer_slug.py`, `analyzer_genre.py`, `debug.py`, `filter.py`, `cleaner.py`, `add_env.py`, `get_slug.py`, `convert_genre_to_flat.py`, `web_analyzer.py`, `test.py`

### 🤖 Agent

- `agent/runner.py`, `agent/cron.py`, `agent/scraper.py`, `agent/config.py`
- Windows Task Scheduler integration

### 🗄️ Database Models

- `Anime`, `Episode`, `DownloadLink`, `Report`, `User`, `ApiKey`

### 🧪 Tests

- 7 files: `test_api.py`, `test_cache.py`, `test_db.py`, `test_fetcher.py`, `test_parser.py`, `test_security.py`, `conftest.py`

### 🎨 Web Portal

- 4 HTML + 4 assets

---

## 🔧 Bug Fixes (Sebelum 1.0.0)

- **API Key vs Bearer conflict** — `bin/_fix_api_js_conflict.py`
- **Syntax error `app.js`** — `bin/_fix_appjs_syntax.py`
- **SQLite database locked** — `bin/_fix_db_lock.py`
- **Bearer support** — `bin/_fix_deps_bearer.py`
- **get-key bind user_id** — `bin/_fix_getkey_userid.py`
- **`max_requests` param** — `bin/_fix_max_requests.py`
- **Regenerate `icons.js`** — `bin/_regen_icons.py`

---

## 📌 Catatan Versi

### Versioning

Format: `MAJOR.MINOR.PATCH`

- **MAJOR** — perubahan breaking
- **MINOR** — fitur baru (backward compatible)
- **PATCH** — bug fix & dokumentasi

### Roadmap Berikutnya

#### 🔴 Prioritas Tinggi

- [ ] **v1.1.0** — Search Flow v2:
  - `poll_url` + `retry_after` di response 404
  - Parameter `?wait=true`
  - Auto-polling di `empty.html`
  - Fallback slug dari query
- [ ] **Fix 3 anime rusak** di DB (`one-piece`, `naruto`, `jujutsu-kaisen`)
- [ ] **Fix `core/pipeline.py`** — validasi metadata
- [ ] **Fix slug agent** — hapus slug salah
- [ ] **Fix `search_live()`** parser — masih return 0 untuk `naruto`
- [ ] **Update `agent/config.py`** — reflect slug yang benar

#### 🟡 Prioritas Sedang

- [ ] **Kuramanime** parser
- [ ] **AnimeIndo** parser
- [ ] **Fix parser rating** di `core/sources/otakudesu.py`
- [ ] **Refactor `logger.py`** — konsisten dengan `settings`
- [ ] **Unifikasi `get_db()`** — 3 varian

#### 🟢 Prioritas Rendah

- [ ] **JWT** untuk stateless auth
- [ ] **Redis** untuk distributed cache
- [ ] **Docker** deployment
- [ ] **Alembic** untuk migrasi DB
- [ ] **bcrypt/argon2** untuk password hashing
- [ ] **QR Code** untuk copyright verification
- [ ] **Blockchain/IPFS** untuk timestamp permanen
- [ ] **PostgreSQL** migration

---

## 🎯 Status Versi

| Versi | Tanggal | Status | Fokus |
|-------|---------|--------|-------|
| **1.1.0** | 2026-10-XX | 🔵 **Planned** | **Search Flow v2** |
| 1.0.7 | 2026-10-10 | ✅ **Active** | Database Lock Fix |
| 1.0.6 | 2026-10-10 | ✅ Stable | API Key Required |
| 1.0.5 | 2026-10-10 | ✅ Stable | Backend Agent Trigger |
| 1.0.4 | 2026-10-10 | ✅ Stable | Error Handling Pages |
| 1.0.3 | 2026-10-10 | ✅ Stable | MD Folder Web Access |
| 1.0.2 | 2026-10-09 | ✅ Stable | Documentation & CORS Fix |
| 1.0.1 | 2026-10-08 | ✅ Stable | Method Restriction |
| 1.0.0 | 2026-10-06 | ✅ Stable | Initial Release |

---

## 🎯 Status Komponen

| Komponen | Status | Versi Terakhir |
|----------|--------|----------------|
| **API Core** | ✅ Stable | 1.0.0 |
| **API Key Required** | ✅ Aktif | 1.0.6 |
| **Rate Limit** | ✅ Aktif | 1.0.6 |
| **Database Layer** | ✅ Rewrite | 1.0.7 |
| **Database Lock** | ✅ Fixed | 1.0.7 |
| **Method Restriction** | ✅ Aktif | 1.0.1 |
| **CORS** | ✅ Fixed | 1.0.2 |
| **Middleware Order** | ✅ Fixed | 1.0.2 |
| **Agent Trigger (Backend)** | ✅ Aktif | 1.0.5 |
| **Search Flow v2** | 🔵 Planned | 1.1.0 |
| **Error Pages** | ✅ Aktif | 1.0.4 |
| **Cache** | ✅ Aktif | 1.0.0 |
| **Auth** | ✅ Aktif | 1.0.0 |
| **Portal** | ✅ Aktif | 1.0.0 |
| **License Page** | ✅ Aktif | 1.0.2 |
| **MD Folder** | ✅ Aktif | 1.0.3 |
| **Scraper** | ✅ Aktif | 1.0.0 |
| **Agent** | ✅ Aktif | 1.0.0 |
| **Tests** | ✅ 45+ | 1.0.1 |
| **Docs** | ✅ Lengkap | 1.0.3 |

---

## 📋 Cara Update Changelog

Setiap perubahan baru, tambahkan section di atas:

```markdown
## [X.Y.Z] — YYYY-MM-DD — Judul Singkat

### Added
- Fitur baru

### Changed
- Perubahan behavior

### Fixed
- Bug fix

### Removed
- Yang dihapus

### Security
- Update security
```

### Contoh Kenaikan Versi

| Perubahan | Versi Baru |
|-----------|------------|
| Tambah fitur baru | `x.Y+1.0` |
| Fix bug | `x.y.Z+1` |
| Breaking change | `X+1.0.0` |
| Dokumentasi saja | `x.y.Z+1` |

---

## 🔗 Referensi File Terkait

| File | Fungsi |
|------|--------|
| `MD/identity.md` | Identitas project |
| `MD/LICENSE.md` | Lisensi resmi |
| `MD/copyright.md` | Copyright digital |
| `MD/information.md` | Info teknis |
| `MD/usage.md` | Panduan API (JavaScript) |
| `MD/note.md` | Command reference |
| `MD/CHANGELOG.md` | **File ini** |

---

## 📞 Kontak

| Kanal | Info |
|-------|------|
| **Organisasi** | Anicorporation.img |
| **Developer** | Anikuze Ryuuzen |
| **Founder** | Lio Syberion |
| **Ex-Org** | SyberEco.corp.ind |
| **Ex-Founder** | Syres Alona |
| **API** | https://aniwatch.share.zrok.io |
| **Docs** | https://aniwatch.share.zrok.io/docs |
| **MD** | https://aniwatch.share.zrok.io/md |
| **Year** | ©2026 |

---

**Terakhir diupdate:** 2026-10-10
**Versi saat ini:** 1.0.7
**Versi selanjutnya:** 1.1.0 (planned)
**Status:** ✅ Stable

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ANICORPORATION.IMG — ANIWATCH
    Changelog v1.0.7 → v1.1.0 (planned)
    ©2026 — All Rights Reserved

    Developer: Anikuze Ryuuzen
    Founder: Lio Syberion

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```