# 📝 Changelog — AniWatch API

Semua perubahan penting pada project AniWatch didokumentasikan di file ini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/),
versi mengikuti [Semantic Versioning](https://semver.org/).

---

## [1.4.0] — 2026-10-31 — Manual Data Editor & Sinkronisasi

### 🎯 Added — Tool Edit Data (CLI)

- **`tools/edit_anime.py`** — Menambahkan fitur edit data anime manual (berdasarkan ID).
  - Alur: Cari ID → Tampilkan Detail → Pilih Field (Judul, Hari, Genre, dll) → Simpan.
- **`tools.bat`** — Menambahkan menu `[3] data_edit` untuk mengakses tool di atas.

### 🔧 Changed

- **`tools/get_slug.py`** — Fungsi simpan ke `agent/.env` dibatasi maksimal 20 slot (FIFO). Jika sudah 20, slug terlama akan diganti.
- **`agent/runner.py`** — Auto-save ongoing dibatasi 20 slot dan mengecek duplikat sebelum menulis ke `.env`.

### 🐛 Fixed

- **Database** — Memastikan skema database baru (`broadcast_day`) terinisialisasi dengan benar.
- **`api/routes/now.py`** — Memisahkan fungsi `/share/now` (hanya update terbaru) dan `/share/day/{hari}` (jadwal harian).

---

## [1.3.0] — 2026-10-31 — Jadwal Harian & Sinkronisasi Data

### 🎯 Added — Endpoint Jadwal Harian

Menanggapi keluhan Client (Aestracorps.ITX) terkait ketidakmampuan melakukan sortir karena tidak adanya jadwal tayang:
- **Endpoint Baru:** `GET /share/day/{hari}`.
- Mendukung filter: `senin`, `selasa`, `rabu`, `kamis`, `jumat`, `sabtu`, `minggu`.
- Mendukung Pagination (`?page=1&limit=10`).

### 🔧 Changed

- **`/share/now`** — Sekarang difokuskan hanya untuk **anime terbaru (update terakhir)**. Filter hari dihapus dari endpoint ini.
- **Database** — Menambahkan kolom `broadcast_day` pada tabel `anime`.
- **Scraper Otakudesu** — Memperbarui parser untuk mengekstrak informasi jadwal tayang (`Jadwal`/`Hari`).
- **`api/services/now_service.py`** — Memisahkan fungsi `get_now_ongoing` dan `get_anime_by_day`.

---

## [1.2.0] — 2026-10-29 — Pagination & Client Optimization

### 🎯 Added — Pagination (Max 10 Item)

- **Endpoint `/share/now`** — Mendukung `?page=1&limit=10`.
- **Endpoint `/share/season/{season}`** — Mendukung `?page=1&limit=10`.
- **Endpoint `/share/episodeid/{slug}`** — Mendukung `?page=1&limit=10`.
- **Format Response Baru** — `data.items` dan `data.pagination`.

### 🔧 Changed

- **Endpoint `/share/anime/{slug}`** — Jika `?include_episodes=true`, API membatasi maksimal **10 episode** agar tidak OOM (Out of Memory).
- **`main.py`** — Menambahkan `GZipMiddleware` (kompresi JSON > 1KB).
- **`MD/usage.md`** — Update dokumentasi pagination.

---

## [1.1.0] — 2026-10-12 — Agent 3 Modes

### 🎯 Added — Agent 3 Mode

- **Opsi 1: Agent Caller** — Scrape on-demand 1 slug.
- **Opsi 2: Follow .env** — Scrape slug dari config + ongoing.
- **Opsi 3: Hybrid** — Auto switch (caller prioritas tinggi).

### 🆕 File Baru

- `agent/state.py`, `agent/logger.py`, `agent/caller.py`, `agent/coordinator.py`.

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
- **MINOR** — fitur baru.
- **PATCH** — bug fix & dokumentasi.

### Roadmap Berikutnya
- [ ] **Kuramanime** parser.
- [ ] **AnimeIndo** parser.
- [ ] **JWT** untuk stateless auth.
- [ ] **Redis** untuk distributed cache.

---

**Terakhir diupdate:** 2026-10-31
**Versi saat ini:** 1.4.0
**Status:** ✅ Stable

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ANICORPORATION.IMG — ANIWATCH
    Changelog v1.4.0
    ©2026 — All Rights Reserved

    Developer: Anikuze Ryuuzen
    Founder: Lio Syberion

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```