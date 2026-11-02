
# 🎌 AniWatch API — Usage Guide (JavaScript)

Panduan lengkap pakai AniWatch API dari JavaScript (Browser & Node.js).

> **Version:** 1.5.0
> **Base URL:** `https://aniwatch.share.zrok.io` (public) · `http://localhost:8000` (local)
> **Method Restriction:** Hanya `GET` & `POST`

---

## 🚀 Quick Start

```javascript
const API_KEY = "anw_xxxxxxxxxxxxxxxxxxxx";

// Fetch 1 anime
const res = await fetch("http://localhost:8000/share/anime/yowaki-max-sub-indo", {
  headers: { "X-API-Key": API_KEY }
});
const json = await res.json();
console.log(json.data.metadata.title);
```

---

📦 Response Format

Semua response menggunakan format wrapper:

```javascript
{
  success: boolean,
  data: object | null,
  meta: { timestamp, cached, source, duration_ms },
  error: null | { code, message, status, details }
}
```

---

📄 Pagination & Batasan Data

Untuk mencegah OOM, endpoint list dibatasi maksimal 10 item per halaman.

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

Endpoint yang Mendukung Pagination:

· /share/now, /share/season/{season}, /share/episodeid/{slug}, /share/day/{hari}

---

📅 Jadwal Harian (Update v1.5.0)

Sejak v1.3.0, endpoint /share/now hanya mengembalikan anime yang baru di-update. Untuk melihat jadwal tayang, gunakan endpoint khusus /share/day/{hari}.

Endpoint: GET /share/day/{hari}?page=1&limit=10

Hari yang didukung: senin, selasa, rabu, kamis, jumat, sabtu, minggu.

Contoh:

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

🚨 Error Handling

Code HTTP Penyebab
HTTP_401 401 API Key tidak valid / tidak ada
HTTP_405 405 Method PUT/DELETE/PATCH diblokir
HTTP_429 429 Rate limit terlampaui
NO_RESULT 204 Hasil pencarian kosong
VALIDATION_ERROR 422 Format request salah

---

©2026 Anicorporation.img
en
