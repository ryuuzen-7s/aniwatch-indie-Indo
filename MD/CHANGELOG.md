# 📝 Changelog — AniWatch API

Semua perubahan penting pada project AniWatch didokumentasikan di file ini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/),
versi mengikuti [Semantic Versioning](https://semver.org/).

---

## [1.2.0] — 2026-10-29 — Pagination & Client Optimization

### 🎯 Added — Pagination (Max 10 Item)

- **Endpoint `/share/now`** — Sekarang mendukung `?page=1&limit=10`. Client tidak akan menerima seluruh data ongoing sekaligus.
- **Endpoint `/share/season/{season}`** — Mendukung `?page=1&limit=10` untuk mencegah *loading* berlebih pada aplikasi client.
- **Endpoint `/share/episodeid/{slug}`** — Mendukung `?page=1&limit=10` (sebelumnya mengembalikan semua episode dalam 1 JSON).
- **Format Response Baru** — Endpoint paginasi kini mengembalikan `data.items` dan `data.pagination` (total, page, per_page, total_pages).

### 🔧 Changed — Limit Data Episode

- **Endpoint `/share/anime/{slug}`** — Jika client meminta `?include_episodes=true`, API sekarang **membatasi maksimal 10 episode** (parameter `episode_limit`) agar tidak mengirim 1000+ episode (seperti pada One Piece) yang menyebabkan *Out of Memory* (OOM).

### ⚡ Performance — GZip Compression

- **`main.py`** — Menambahkan `GZipMiddleware`. Semua response JSON yang berukuran > 1KB akan dikompresi secara otomatis.
- **Efek:** Ukuran data yang ditransfer ke jaringan berkurang hingga **80-90%** (misal: dari 500 KB menjadi 50 KB), sangat menghemat kuota dan mempercepat loading aplikasi client.

### 📄 Changed — Dokumentasi

- **`MD/usage.md`** — Update contoh penggunaan JavaScript untuk menangani pagination (`data.items`).

---

## [1.1.1] — 2026-10-28 — Task Scheduler & Agent Fix

### 🔧 Changed

- **`agent/runner.py`** — Auto-save ongoing sekarang dibatasi **maksimal 20 slug** di `.env`. Jika sudah 20, slug terlama akan diganti (FIFO).
- **`tools/get_slug.py`** — Fitur simpan ke `.env` sekarang mengecek duplikat dan membatasi maksimal 20 item.
- **`tools.bat`** — Tambah menu `[15] auto_slug` untuk mempermudah update slug ke `agent/.env`.

### 🐛 Fixed

- **Agent Runner** — Memastikan `follow_all=True` agar anime dengan banyak episode (lebih dari 1) di-scrape seluruhnya, bukan hanya episode 1.

---

## [1.1.0] — 2026-10-12 — Agent 3 Modes

### 🎯 Added — Agent 3 Mode

- **Opsi 1: Agent Caller** — Scrape on-demand 1 slug yang dipanggil.
- **Opsi 2: Follow .env** — Scrape slug dari config + ongoing.
- **Opsi 3: Hybrid** — Auto switch (caller prioritas tinggi, pause follow_env sementara).

### 🆕 File Baru

- `agent/state.py` — State sharing antar mode.
- `agent/logger.py` — Setup logging.
- `agent/caller.py` — Mode Agent Caller.
- `agent/coordinator.py` — Mode Hybrid.

### 🗑️ File Hapus (Legacy)

- `agent/base.py`
- `agent/otakudesu.py`
- `agent/worker.py`

---

## [1.0.9] — 2026-10-11 — HTTP Status Codes (Search)

### 🎯 Changed — Search Response

- **200 OK** — Data ada di DB.
- **202 Accepted** — Data sedang di-scrape (header `Retry-After`).
- **204 No Content** — Tidak ada hasil & tidak bisa scrape.
- **404** — Tidak dipakai lagi untuk query kosong.

### 🔧 Changed

- **`api/routes/search.py`** — Flow: DB → running check → trigger → 202/204.
- **`web/assets/api.js`** — Handle 202 (processing) & 204 (not found).

---

## [1.0.8] — 2026-10-11 — Search Service Rewrite

### 🔧 Rewrite

- **`api/services/search_service.py`** — Tulis ulang total.
- **Tambah:** `is_scrape_running()`, `wait_for_scrape()`, `get_running_slugs()`.
- **Fix:** Parser `search_live()` — handle `<h2><a>` + extract parent slug dari episode.
- **Fix:** `trigger_agent_worker()` — retry DB lock + global lock.

---

## [1.0.7] — 2026-10-10 — Database Lock Fix & DB Layer Rewrite

### 🐛 Fixed — Database Lock

- **Masalah:** `database is locked` saat force scrape + agent worker barengan.
- **Fix:** Global write lock (`db/lock.py`), Retry decorator (`@with_retry`), Busy timeout 60s.

### ✏️ File Update

- `db/database.py`, `db/models.py`, `db/repository.py`, `db/__init__.py`.

---

## [1.0.6] — 2026-10-10 — API Key Required

### 🔒 Security — Wajib API Key

- **Endpoint `/share/*` WAJIB API key** (`X-API-Key` header).
- Tanpa API key → **401 Unauthorized**.
- Endpoint publik (`/`, `/health`, `/stats`, `/docs`) tetap bisa diakses.

### 📊 Rate Limit Baru

- Anonymous: 10 req/menit (dari 30).
- API Key: Mengikuti settingan DB.

---

## [1.0.5] — 2026-10-10 — Backend Agent Trigger

### 🎯 Added

- **404 + Agent Trigger** di `/share/query` saat hasil kosong.
- Endpoint baru: `/share/scrape-status/{slug}` dan `/share/scrape-jobs`.

---

## [1.0.4] — 2026-10-10 — Error Handling Pages

### 🎯 Added

- **`web/error/index.html`** — Halaman query error.
- **`web/error/empty.html`** — Halaman empty result + trigger agent.

---

## [1.0.3] — 2026-10-10 — MD Folder Web Access

### 📚 Added

- Folder `MD/` bisa diakses via web (`/md/`).
- `MD/index.html` — Halaman listing markdown.

---

## [1.0.2] — 2026-10-09 — Documentation & CORS Fix

### 📚 Added

- `usage.md`, `identity.md`, `LICENSE.md`, `copyright.md`, `information.md`, `note.md`.

### 🔧 Fixed — CORS Preflight

- `OPTIONS /health` → 400 → **200 OK** (tambah `allow_origin_regex`).
- Urutan middleware dibalik: CORS paling luar.

---

## [1.0.1] — 2026-10-08 — Method Restriction

### 🎯 Added

- Middleware `MethodRestrictorMiddleware` (`api/middleware/method_restrictor.py`).
- Hanya `GET` & `POST`.
- `PUT`/`DELETE`/`PATCH` → 405.
- Exclude: `/keys`, `/docs`, `/redoc`, `/openapi.json`, `/monitor`.

---

## [1.0.0] — 2026-10-06 — Initial Release

### 🎉 Added — Fitur Utama

- FastAPI + SQLAlchemy + Pydantic v2.
- SQLite dengan WAL mode.
- Scraper Otakudesu.
- Cache 2-tier (Memory + File).
- Rate limiter.
- Auth: API Key + Session + Bearer.
- Web portal + Monitoring dashboard.

---

## 📌 Catatan Versi

### Versioning

Format: `MAJOR.MINOR.PATCH`

- **MAJOR** — perubahan breaking.
- **MINOR** — fitur baru (backward compatible).
- **PATCH** — bug fix & dokumentasi.

### Roadmap Berikutnya

- [ ] **Kuramanime** parser (`core/sources/kuramanime.py`).
- [ ] **AnimeIndo** parser (`core/sources/animeindo.py`).
- [ ] **JWT** untuk stateless auth.
- [ ] **Redis** untuk distributed cache.
- [ ] **Docker** deployment.
- [ ] **Alembic** untuk migrasi DB.
- [ ] **Fix** parser rating di `core/sources/otakudesu.py`.

---

## 🎯 Status Versi

| Versi | Tanggal | Status | Fokus |
|-------|---------|--------|-------|
| **1.2.0** | 2026-10-29 | ✅ **Active** | **Pagination & GZip** |
| 1.1.1 | 2026-10-28 | ✅ Stable | Agent Fix |
| 1.1.0 | 2026-10-12 | ✅ Stable | Agent 3 Modes |
| 1.0.9 | 2026-10-11 | ✅ Stable | HTTP Status Codes |
| 1.0.8 | 2026-10-11 | ✅ Stable | Search Service Rewrite |
| 1.0.7 | 2026-10-10 | ✅ Stable | Database Lock Fix |
| 1.0.6 | 2026-10-10 | ✅ Stable | API Key Required |
| 1.0.5 | 2026-10-10 | ✅ Stable | Backend Agent Trigger |
| 1.0.4 | 2026-10-10 | ✅ Stable | Error Pages |
| 1.0.3 | 2026-10-10 | ✅ Stable | MD Folder |
| 1.0.2 | 2026-10-09 | ✅ Stable | Docs & CORS Fix |
| 1.0.1 | 2026-10-08 | ✅ Stable | Method Restriction |
| 1.0.0 | 2026-10-06 | ✅ Stable | Initial Release |

---

**Terakhir diupdate:** 2026-10-29
**Versi saat ini:** 1.2.0
**Status:** ✅ Stable

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ANICORPORATION.IMG — ANIWATCH
    Changelog v1.2.0
    ©2026 — All Rights Reserved

    Developer: Anikuze Ryuuzen
    Founder: Lio Syberion

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```