# 📝 Changelog — AniWatch API

Semua perubahan penting pada project AniWatch didokumentasikan di file ini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/),
versi mengikuti [Semantic Versioning](https://semver.org/).

---

## [1.0.1] — 2026-10-08 — Method Restriction

### 🎯 Added — Middleware Method Restrictor

Menambahkan middleware baru untuk **membatasi HTTP method** hanya ke `GET` & `POST`.

**File baru:**
- `api/middleware/method_restrictor.py` (~107 baris)
  - Class `MethodRestrictorMiddleware`
  - Configurable via `.env`
  - Auto-format error via `exceptions.py`
  - Skip `OPTIONS` & `HEAD` (CORS preflight & health check)
  - Path exclusion support (`/keys`, `/docs`, dll)

**File dimodifikasi:**

| File | Perubahan |
|------|-----------|
| `api/middleware/__init__.py` | Export `MethodRestrictorMiddleware` |
| `config.py` | Tambah `allowed_methods`, `method_excluded_paths` + 2 property |
| `main.py` | Import + daftar middleware + update CORS `allow_methods` |
| `.env.example` | Section `API METHOD RESTRICTION` |
| `test/test_api.py` | Class `TestMethodRestrictor` (13 test) |
| `.env` | Setting baru (manual update) |

### 🔒 Security — Method Restriction

- `PUT` → **405 Method Not Allowed**
- `DELETE` → **405** (kecuali `/keys/*`)
- `PATCH` → **405**
- `OPTIONS` → ✅ Allowed
- `HEAD` → ✅ Allowed

**Path dikecualikan:**
- `/keys` — untuk revoke API key
- `/docs`, `/redoc`, `/openapi.json` — dokumentasi
- `/monitor`, `/monitor/static` — dashboard

### 🔧 Changed

- **CORS** `allow_methods`:
  - ❌ Sebelum: `["GET", "POST", "PUT", "DELETE", "OPTIONS"]`
  - ✅ Sesudah: `["GET", "POST", "OPTIONS"]`
- **Middleware order** (dari luar ke dalam):
  ```
  CORS → MethodRestrictor → RateLimit → Routes
  ```

### ✅ Tests

- **13 test baru** di `test/test_api.py`:
  - `test_method_not_allowed_share` (PUT, DELETE, PATCH)
  - `test_method_not_allowed_health` (PUT, DELETE, PATCH)
  - `test_allow_header`
  - `test_get_still_works`
  - `test_options_allowed`
  - `test_excluded_path_delete`
  - `test_docs_accessible`
  - `test_openapi_accessible`
  - `test_share_post_allowed`

### 📊 Verifikasi

```cmd
tools.bat verify
```

| Method | Endpoint | Status | Hasil |
|--------|----------|--------|-------|
| GET | /health | 200 | ✅ |
| PUT | /share/now | 405 | ✅ |
| DELETE | /share/now | 405 | ✅ |
| PATCH | /share/now | 405 | ✅ |
| DELETE | /keys/999 | 401/403/404 | ✅ (excluded) |
| GET | /openapi.json | 200 | ✅ |
| OPTIONS | /share/now | 200/204 | ✅ |

---

## [1.0.0] — 2026-10-XX — Initial Release

### 🎉 Added — Fitur Utama

- **FastAPI** based REST API
- **SQLite** dengan WAL mode
- **Scraper** Otakudesu (`core/sources/otakudesu.py`)
- **Cache layer** 2-tier (memory + file)
- **Rate limiter** in-memory sliding window
- **Auth**: API Key + Session + Bearer
- **Web portal** (`/portal`)
- **Monitoring dashboard** (`/monitor`)
- **Swagger UI** (`/docs`) + **ReDoc** (`/redoc`)

### 🎯 Endpoints

- `/share/*` — data anime (11 endpoint)
- `/auth/*` — login, register, key management
- `/system/*` — health, stats, root
- `/cache/*` — cache control
- `/rate-limit/*` — rate limit control
- `/admin/*` — admin panel

### 🛠️ Tools

- `tools/db_monitor.py` — monitor DB
- `tools/add_pass.py` — manage API key
- `tools/scanner.py` — scan bug
- `tools/scraper_update.py` — scrape ongoing
- `tools/scraper_by_genre.py` — scrape by genre
- `tools/analyzer_slug.py` — analisa slug
- `tools/analyzer_genre.py` — analisa genre
- `tools/debug.py` — debug parser
- `tools/filter.py` — filter file sampah
- `tools/cleaner.py` — bersihkan folder
- `tools/add_env.py` — edit .env dari JSON
- `tools/get_slug.py` — extract slug
- `tools/convert_genre_to_flat.py` — convert JSON
- `tools/web_analyzer.py` — analisa HTML target

### 🤖 Agent (Auto Scraper)

- `agent/runner.py` — runner utama
- `agent/cron.py` — scheduler internal
- `agent/scraper.py` — scrape 1 anime
- Windows Task Scheduler integration

### 🗄️ Database Models

- `Anime` — metadata anime
- `Episode` — episode + stream
- `DownloadLink` — link download
- `Report` — report error
- `User` — user login
- `ApiKey` — API key

### 🧪 Tests

- `test/test_api.py`
- `test/test_cache.py`
- `test/test_db.py`
- `test/test_fetcher.py`
- `test/test_parser.py`
- `test/test_security.py`

---

## 🔧 Bug Fixes (Sebelum 1.0.0)

### Fixed

- **API Key vs Bearer conflict** — `bin/_fix_api_js_conflict.py`
- **Syntax error `app.js`** — `bin/_fix_appjs_syntax.py`
- **SQLite database locked** — `bin/_fix_db_lock.py` (retry + WAL mode)
- **Bearer support di `security/deps.py`** — `bin/_fix_deps_bearer.py`
- **get-key bind user_id dari session** — `bin/_fix_getkey_userid.py`
- **`max_requests` param di `generate_api_key`** — `bin/_fix_max_requests.py`
- **Regenerate `icons.js`** — `bin/_regen_icons.py`

---

## 📌 Catatan Versi

### Versioning

Format: `MAJOR.MINOR.PATCH`

- **MAJOR** — perubahan breaking
- **MINOR** — fitur baru (backward compatible)
- **PATCH** — bug fix

### Roadmap Berikutnya

- [ ] **Kuramanime** parser (`core/sources/kuramanime.py`)
- [ ] **AnimeIndo** parser (`core/sources/animeindo.py`)
- [ ] **JWT** untuk stateless auth
- [ ] **Redis** untuk distributed cache
- [ ] **Docker** deployment
- [ ] **Alembic** untuk migrasi DB
- [ ] **bcrypt/argon2** untuk password hashing
- [ ] **Refactor** `logger.py` & `config.py` (legacy cleanup)
- [ ] **Fix** 3 varian `get_db()` (unifikasi)

---

## 🎯 Status Saat Ini

| Komponen | Status |
|----------|--------|
| **API** | ✅ Stable |
| **Method Restriction** | ✅ Aktif (v1.0.1) |
| **Cache** | ✅ Aktif |
| **Rate Limit** | ✅ Aktif |
| **Auth** | ✅ Aktif |
| **Portal** | ✅ Aktif |
| **Scraper** | ✅ Aktif |
| **Tests** | ✅ 45+ test |
| **Docs** | ✅ Lengkap |

---

## 📋 Cara Update Changelog

Kalau ada perubahan baru, tambahkan section di atas:

```markdown
## [X.Y.Z] — YYYY-MM-DD — Judul Singkat

### Added
- Fitur baru

### Changed
- Perubahan

### Fixed
- Bug fix

### Removed
- Yang dihapus

### Security
- Update security
```

---

**Terakhir diupdate:** 2026-10-08
**Versi saat ini:** 1.0.1
**Status:** ✅ Stable