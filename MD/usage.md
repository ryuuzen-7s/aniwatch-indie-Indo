# 🎌 AniWatch API — Usage Guide (JavaScript)

Panduan lengkap pakai AniWatch API dari JavaScript (Browser & Node.js).

> **Version:** 1.3.0
> **Base URL:** `https://aniwatch.share.zrok.io` (public) · `http://localhost:8000` (local)
> **Method Restriction:** Hanya `GET` & `POST`

---

## 📋 Daftar Isi

1. [Quick Start](#-quick-start)
2. [Authentication](#-authentication)
3. [Response Format](#-response-format)
4. [Anime Endpoints](#-anime-endpoints)
5. [Pagination & Batasan Data](#-pagination--batasan-data)
6. [Jadwal Harian (BARU)](#-jadwal-harian-baru)
7. [Error Handling](#-error-handling)

---

## 🚀 Quick Start

```javascript
// Fetch 1 anime
const res = await fetch("http://localhost:8000/share/anime/yowaki-max-sub-indo");
const json = await res.json();

console.log(json.data.metadata.title);
```

---

## 🔐 Authentication

Semua request ke `/share/*` butuh header API Key:

```javascript
const API_KEY = "anw_xxxxxxxxxxxxxxxxxxxx";

const res = await fetch("http://localhost:8000/share/now", {
  headers: {
    "X-API-Key": API_KEY,
  },
});
```

---

## 📦 Response Format

Semua response menggunakan format wrapper:

```javascript
{
  success: boolean,
  data: object | null,
  meta: { ... },
  error: null | { code, message, status, details }
}
```

---

## 🎬 Anime Endpoints

### 1. Detail Anime
**`GET /share/anime/{slug}`**

> **Catatan:** Jika menggunakan `?include_episodes=true`, API akan membatasi maksimal **10 episode** pertama agar tidak memberatkan client.

### 2. Poster Anime
**`GET /share/posterid/{slug}`**

### 3. Pencarian
**`GET /share/query?q={keyword}`**

- `200 OK` — Data ada di DB.
- `202 Accepted` — Data sedang di-scrape di background.
- `204 No Content` — Tidak ada hasil.

---

## 📄 Pagination & Batasan Data

Untuk mencegah **Out of Memory (OOM)** pada aplikasi client, endpoint list dibatasi **maksimal 10 item per halaman**.

Format Response Pagination:
```javascript
{
  "success": true,
  "data": {
    "items": [ ... ], // List data (max 10)
    "pagination": {
      "total": 100,
      "page": 1,
      "per_page": 10,
      "total_pages": 10
    }
  }
}
```

### Endpoint yang Mendukung Pagination:
- `/share/now` (Anime update terbaru)
- `/share/season/{season}` (Anime per season)
- `/share/episodeid/{slug}` (List episode)
- `/share/day/{hari}` (Jadwal harian)

**Cara Pakai:**
```javascript
const res = await fetch("http://localhost:8000/share/episodeid/naruto?page=2&limit=10", {
  headers: { "X-API-Key": API_KEY }
});
const data = await res.json();
console.log(data.data.items); // 10 episode di halaman 2
```

---

## 📅 Jadwal Harian (BARU)

Sesuai pembaruan v1.3.0, endpoint `/share/now` sekarang **hanya** mengembalikan anime yang baru di-update. Untuk melihat jadwal tayang, gunakan endpoint khusus `/share/day/{hari}`.

**Endpoint:** `GET /share/day/{hari}?page=1&limit=10`

**Hari yang didukung:** `senin`, `selasa`, `rabu`, `kamis`, `jumat`, `sabtu`, `minggu`.

**Contoh:**
```javascript
// Mengambil anime yang tayang hari Senin
const res = await fetch("http://localhost:8000/share/day/senin?page=1&limit=10", {
  headers: { "X-API-Key": API_KEY }
});
const data = await res.json();

console.log(`Total anime hari Senin: ${data.data.pagination.total}`);
console.log(data.data.items);
```

---

## 🚨 Error Handling

| Code | HTTP | Penyebab |
|------|------|----------|
| `HTTP_401` | 401 | API Key tidak valid / tidak ada |
| `HTTP_405` | 405 | Method PUT/DELETE/PATCH diblokir |
| `HTTP_429` | 429 | Rate limit terlampaui |
| `NO_RESULT` | 204 | Hasil pencarian kosong |
| `VALIDATION_ERROR` | 422 | Format request salah |

---

**©2026 Anicorporation.img**
**Developer:** Anikuze Ryuuzen