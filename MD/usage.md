# 🎌 AniWatch API — Usage Guide (JavaScript)

Panduan lengkap pakai AniWatch API dari JavaScript (Browser & Node.js).

> **Version:** 1.0.1
> **Base URL:** `https://aniwatch.share.zrok.io` (public) · `http://localhost:8000` (local)
> **Method Restriction:** Hanya `GET` & `POST` (sejak v1.0.1)

---

## 📋 Daftar Isi

1. [Quick Start](#-quick-start)
2. [Authentication](#-authentication)
3. [Response Format](#-response-format)
4. [Anime Endpoints](#-anime-endpoints)
5. [Episode Endpoints](#-episode-endpoints)
6. [Search & Discovery](#-search--discovery)
7. [Report & Scrape](#-report--scrape)
8. [Auth & API Key](#-auth--api-key)
9. [Cache & Rate Limit](#-cache--rate-limit)
10. [Error Handling](#-error-handling)
11. [Method Restriction](#-method-restriction)

---

## 🚀 Quick Start

### Browser (Fetch API)

```javascript
// Fetch 1 anime
const res = await fetch("http://localhost:8000/share/anime/yowaki-max-sub-indo");
const json = await res.json();

console.log(json.data.metadata.title);
// Output: "Yowaki Max Subtitle Indonesia"
```

### Node.js (Native Fetch, Node 18+)

```javascript
const res = await fetch("http://localhost:8000/share/anime/yowaki-max-sub-indo");
const { data } = await res.json();

console.log(data.metadata.title);
```

### Node.js (Axios)

```bash
npm install axios
```

```javascript
const axios = require("axios");

const { data } = await axios.get(
  "http://localhost:8000/share/anime/yowaki-max-sub-indo"
);

console.log(data.data.metadata.title);
```

---

## 🔐 Authentication

AniWatch punya 3 cara autentikasi:

| Cara | Header | Untuk |
|------|--------|-------|
| **API Key** | `X-API-Key: anw_xxx` | Server-to-server, bot |
| **Bearer Token** | `Authorization: Bearer xxx` | Mobile app |
| **Session Cookie** | `aniwatch_session` (auto) | Browser portal |

### Contoh: Pakai API Key

```javascript
const API_KEY = "anw_xxxxxxxxxxxxxxxxxxxx";

const res = await fetch("http://localhost:8000/me", {
  headers: {
    "X-API-Key": API_KEY,
  },
});

const json = await res.json();
console.log(json.data);
```

**Response:**
```json
{
  "success": true,
  "data": {
    "authenticated": true,
    "method": "api_key",
    "user_id": null,
    "username": null,
    "role": "user",
    "key_prefix": "anw_xxxxxxxx"
  },
  "meta": {...},
  "error": null
}
```

### Contoh: Pakai Bearer Token

```javascript
const TOKEN = "your-session-token";

const res = await fetch("http://localhost:8000/me", {
  headers: {
    "Authorization": `Bearer ${TOKEN}`,
  },
});
```

### Contoh: Login + Cookie (Browser)

```javascript
// Login
const res = await fetch("http://localhost:8000/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "include",   // ← penting untuk cookie
  body: JSON.stringify({
    username: "testuser",
    password: "test123456",
  }),
});

const json = await res.json();

if (json.success) {
  // Cookie aniwatch_session otomatis tersimpan
  localStorage.setItem("aniwatch_token", json.data.token);
  localStorage.setItem("aniwatch_user", JSON.stringify(json.data.user));
}
```

---

## 📦 Response Format

Semua response pakai format **wrapper**:

```javascript
{
  success: boolean,     // true = sukses, false = error
  data: object | null,  // isi data
  meta: {
    timestamp: string,  // ISO 8601
    cached: boolean,    // dari cache?
    source: string,     // "db" | "live" | "cache"
    duration_ms: number // waktu proses
  },
  error: null | {
    code: string,       // "HTTP_405", "VALIDATION_ERROR", dll
    message: string,    // pesan manusiawi
    status: number,     // HTTP status code
    details: object     // info tambahan
  }
}
```

### Helper: Cek Response

```javascript
async function callAPI(url, options = {}) {
  const res = await fetch(url, options);
  const json = await res.json();

  if (!json.success) {
    throw new Error(`[${json.error.code}] ${json.error.message}`);
  }

  return json.data;
}
```

**Pakai:**
```javascript
try {
  const data = await callAPI("http://localhost:8000/share/anime/naruto-sub-indo");
  console.log(data.metadata.title);
} catch (err) {
  console.error("API Error:", err.message);
}
```

---

## 🎬 Anime Endpoints

### 1. Get Anime Detail

**`GET /share/anime/{slug}`**

```javascript
async function getAnime(slug) {
  const res = await fetch(`http://localhost:8000/share/anime/${slug}`);
  const json = await res.json();
  return json.data;
}

const anime = await getAnime("yowaki-max-sub-indo");
console.log(anime.metadata.title);      // "Yowaki Max Subtitle Indonesia"
console.log(anime.metadata.studio);     // "Jumondou"
console.log(anime.metadata.genres);     // ["Isekai", "Romance", "Shoujo"]
console.log(anime.metadata.poster_url); // "https://..."
```

**Query Parameters:**

| Param | Tipe | Default | Deskripsi |
|-------|------|---------|-----------|
| `source` | string | `otakudesu` | Source provider |
| `refresh` | boolean | `false` | Paksa re-scrape |
| `include_episodes` | boolean | `false` | Sertakan list episode |

**Contoh:**
```javascript
const anime = await getAnime("yowaki-max-sub-indo", {
  include_episodes: true,
  refresh: true,
});

// Bangun URL dengan query
const url = new URL("http://localhost:8000/share/anime/yowaki-max-sub-indo");
url.searchParams.set("include_episodes", "true");
url.searchParams.set("refresh", "true");

const res = await fetch(url);
```

---

### 2. Get Poster Anime

**`GET /share/posterid/{slug}`**

```javascript
async function getPoster(slug) {
  const res = await fetch(`http://localhost:8000/share/posterid/${slug}`);
  const json = await res.json();
  return json.data.poster_url;
}

const posterUrl = await getPoster("yowaki-max-sub-indo");
```

**Redirect Mode:**
```javascript
// Redirect langsung ke gambar (302)
const url = `http://localhost:8000/share/posterid/yowaki-max-sub-indo?redirect=true`;
document.getElementById("poster").src = url;
```

---

### 3. Get Anime per Season

**`GET /share/season/{season}`**

Format season: `fall-2026`, `winter-2025`, `2026`

```javascript
async function getSeason(season, limit = 50) {
  const url = `http://localhost:8000/share/season/${season}?limit=${limit}`;
  const res = await fetch(url);
  const json = await res.json();
  return json.data;
}

const season = await getSeason("fall-2026");
console.log(season.season);        // "fall-2026"
console.log(season.year);          // 2026
console.log(season.month_range);   // "OCT-NOV-DEC"
console.log(season.results);       // array anime
console.log(season.total);         // 30
```

---

### 4. Get Anime Ongoing

**`GET /share/now`**

```javascript
async function getNow(limit = 20) {
  const res = await fetch(`http://localhost:8000/share/now?limit=${limit}`);
  const json = await res.json();
  return json.data;
}

const now = await getNow(20);
now.results.forEach((anime) => {
  console.log(`[${anime.latest_episode_number}] ${anime.title}`);
});
```

**Contoh Output:**
```
[5] Naruto
[3] One Piece
[1] Yowaki Max
```

---

## 📺 Episode Endpoints

### 1. Get Episode List

**`GET /share/episodeid/{slug}`**

```javascript
async function getEpisodeList(animeSlug) {
  const res = await fetch(`http://localhost:8000/share/episodeid/${animeSlug}`);
  const json = await res.json();
  return json.data;
}

const list = await getEpisodeList("yowaki-max-sub-indo");
console.log(list.anime_title);       // "Yowaki Max Subtitle Indonesia"
console.log(list.total);             // 12
list.episodes.forEach((ep) => {
  console.log(`Ep ${ep.episode_number}: ${ep.title} (${ep.download_count} dl)`);
});
```

---

### 2. Get Episode Detail

**`GET /share/episode/{number}/{slug}`**

```javascript
async function getEpisode(number, animeSlug) {
  const res = await fetch(
    `http://localhost:8000/share/episode/${number}/${animeSlug}`
  );
  const json = await res.json();
  return json.data;
}

const ep = await getEpisode(1, "yowaki-max-sub-indo");

console.log(ep.title);                       // "Episode 1"
console.log(ep.streams);                     // [{host, url, quality}]
console.log(ep.downloads);                   // [{quality, host, url, is_alive}]
console.log(ep.downloads_summary.total);     // 30
console.log(ep.downloads_summary.alive);     // 28
console.log(ep.downloads_summary.by_quality); // {720p: 10, 480p: 10, 360p: 10}
```

**Query:**
```javascript
// Ringan tanpa download
const ep = await getEpisode(1, "yowaki-max-sub-indo", {
  include_downloads: false,
});

const url = new URL(
  "http://localhost:8000/share/episode/1/yowaki-max-sub-indo"
);
url.searchParams.set("include_downloads", "false");
```

---

## 🔍 Search & Discovery

### 1. Search Anime

**`GET /share/query?q={keyword}`**

```javascript
async function searchAnime(keyword, options = {}) {
  const params = new URLSearchParams({
    q: keyword,
    limit: options.limit || 20,
    live: options.live !== false,
  });

  const res = await fetch(`http://localhost:8000/share/query?${params}`);
  const json = await res.json();
  return json.data;
}

const results = await searchAnime("naruto");
console.log(results.query);          // "naruto"
console.log(results.total);          // 5
console.log(results.from_cache);     // true/false
results.results.forEach((anime) => {
  console.log(`[${anime.slug}] ${anime.title}`);
});
```

**Query Parameters:**

| Param | Tipe | Default | Deskripsi |
|-------|------|---------|-----------|
| `q` | string | **wajib** | Kata kunci (min 2 char) |
| `source` | string | `otakudesu` | Source |
| `limit` | int | 20 | Max hasil (1-100) |
| `live` | bool | `true` | Izinkan live scrape |

---

## 📮 Report & Scrape

### 1. Report Link Error

**`POST /share/errorid/{slug}`**

```javascript
async function reportError(slug, body) {
  const res = await fetch(`http://localhost:8000/share/errorid/${slug}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const json = await res.json();
  return json.data;
}

const report = await reportError("yowaki-max-sub-indo", {
  url: "https://mega.nz/file/xxx",
  reason: "Link sudah mati",
  quality: "720p",
  host: "Mega",
});

console.log(report.id);           // 1
console.log(report.resolved);     // false
```

---

### 2. Force Scrape Anime

**`POST /share/empty/{slug}`**

```javascript
async function forceScrape(slug) {
  const res = await fetch(`http://localhost:8000/share/empty/${slug}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source: "otakudesu",
      follow_all: true,
    }),
  });
  const json = await res.json();
  return json.data;
}

const result = await forceScrape("yowaki-max-sub-indo");
console.log(result.scraped);      // true
console.log(result.anime);        // 1
console.log(result.episodes);     // 12
console.log(result.downloads);    // 360
console.log(result.message);      // "Scrape berhasil"
```

---

### 3. Check Link Availability

**`POST /share/linkask/{slug}`**

```javascript
async function checkLink(slug) {
  const res = await fetch(`http://localhost:8000/share/linkask/${slug}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      type: "all",   // "stream" | "download" | "all"
      deep: false,   // resolve shortener
    }),
  });
  const json = await res.json();
  return json.data;
}

const link = await checkLink("yowaki-max-sub-indo");
console.log(link.has_link);         // true
console.log(link.stream_count);     // 12
console.log(link.download_count);   // 360
console.log(link.alive_count);      // 350
console.log(link.dead_count);       // 10
```

---

## 🔑 Auth & API Key

### 1. Register

**`POST /register`**

```javascript
async function register(username, password, email = "") {
  const res = await fetch("http://localhost:8000/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, email }),
  });
  const json = await res.json();

  if (!json.success) {
    throw new Error(json.error.message);
  }

  return json.data;
}

const user = await register("newuser", "test123456", "test@test.com");
console.log(user.username);   // "newuser"
console.log(user.role);       // "user"
```

---

### 2. Login

**`POST /login`**

```javascript
async function login(username, password) {
  const res = await fetch("http://localhost:8000/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",   // penting untuk cookie
    body: JSON.stringify({ username, password }),
  });
  const json = await res.json();

  if (!json.success) {
    throw new Error(json.error.message);
  }

  // Simpan token & user
  localStorage.setItem("aniwatch_token", json.data.token);
  localStorage.setItem("aniwatch_user", JSON.stringify(json.data.user));

  return json.data;
}

const session = await login("testuser", "test123456");
console.log(session.token);            // "xxxxx"
console.log(session.user.username);    // "testuser"
```

---

### 3. Generate API Key

**`POST /get-key`**

```javascript
async function getApiKey(name = "default", options = {}) {
  const res = await fetch("http://localhost:8000/get-key", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      name,
      rate_limit: options.rate_limit || 100,
      expires_days: options.expires_days || 30,
      max_requests: options.max_requests || null,
    }),
  });
  const json = await res.json();
  return json.data;
}

const result = await getApiKey("my-app", {
  rate_limit: 100,
  expires_days: 90,
});

console.log(result.key);                 // "anw_xxxxx" (SIMPAN!)
console.log(result.info.id);             // 1
console.log(result.info.rate_limit);     // 100
console.log(result.info.expires_at);     // "2027-01-07T..."
```

⚠️ **PENTING:** `result.key` **hanya muncul sekali**! Simpan di tempat aman.

---

### 4. List API Key

**`GET /keys`**

```javascript
async function listKeys(apiKey) {
  const res = await fetch("http://localhost:8000/keys", {
    headers: apiKey ? { "X-API-Key": apiKey } : {},
    credentials: "include",
  });
  const json = await res.json();
  return json.data;
}

const keys = await listKeys();
keys.forEach((k) => {
  console.log(`[${k.id}] ${k.name} (${k.key_prefix}...) — ${k.rate_limit} rpm`);
});
```

---

### 5. Revoke API Key

**`DELETE /keys/{id}`** (kecuali dari method restriction)

```javascript
async function revokeKey(keyId, apiKey) {
  const res = await fetch(`http://localhost:8000/keys/${keyId}`, {
    method: "DELETE",
    headers: apiKey ? { "X-API-Key": apiKey } : {},
    credentials: "include",
  });
  const json = await res.json();
  return json.data;
}

const result = await revokeKey(1);
console.log(result.revoked);   // true
console.log(result.key_id);    // 1
```

---

### 6. Info User Sekarang

**`GET /me`**

```javascript
async function getMe(apiKey) {
  const res = await fetch("http://localhost:8000/me", {
    headers: apiKey ? { "X-API-Key": apiKey } : {},
    credentials: "include",
  });
  const json = await res.json();
  return json.data;
}

const me = await getMe();
console.log(me.authenticated);   // true/false
console.log(me.method);          // "api_key" | "session" | "none"
console.log(me.username);        // "testuser"
console.log(me.role);            // "user"
```

---

### 7. Logout

**`POST /logout`**

```javascript
async function logout() {
  const res = await fetch("http://localhost:8000/logout", {
    method: "POST",
    credentials: "include",
  });
  const json = await res.json();

  // Hapus localStorage
  localStorage.removeItem("aniwatch_token");
  localStorage.removeItem("aniwatch_user");
  localStorage.removeItem("aniwatch_api_key");

  return json.data;
}

await logout();
```

---

## ⚡ Cache & Rate Limit

### 1. Cache Stats

**`GET /cache/stats`**

```javascript
async function getCacheStats() {
  const res = await fetch("http://localhost:8000/cache/stats");
  const json = await res.json();
  return json.data;
}

const stats = await getCacheStats();
console.log(stats.enabled);              // true
console.log(stats.memory.size);          // 42
console.log(stats.memory.hits);          // 1234
console.log(stats.memory.hit_rate);      // 85.5
console.log(stats.file.files);           // 100
```

---

### 2. Clear Cache

**`POST /cache/clear`**

```javascript
async function clearCache() {
  const res = await fetch("http://localhost:8000/cache/clear", {
    method: "POST",
  });
  const json = await res.json();
  return json.data;
}

const result = await clearCache();
console.log(result.memory);    // "cleared"
console.log(result.file);      // 100
```

---

### 3. Invalidate Cache Anime

**`POST /cache/invalidate/{slug}`**

```javascript
async function invalidateAnime(slug, source = "otakudesu") {
  const res = await fetch(
    `http://localhost:8000/cache/invalidate/${slug}?source=${source}`,
    { method: "POST" }
  );
  const json = await res.json();
  return json.data;
}

const result = await invalidateAnime("yowaki-max-sub-indo");
console.log(result.slug);                // "yowaki-max-sub-indo"
console.log(result.invalidated_keys);    // 3
```

---

### 4. Rate Limit Stats

**`GET /rate-limit/stats`**

```javascript
async function getRateLimitStats() {
  const res = await fetch("http://localhost:8000/rate-limit/stats");
  const json = await res.json();
  return json.data;
}

const stats = await getRateLimitStats();
console.log(stats.active_keys);              // 5
console.log(stats.total_requests_tracked);   // 123
```

---

### 5. Cek Header Rate Limit

Setiap response punya header ini:

```javascript
const res = await fetch("http://localhost:8000/share/now");

console.log(res.headers.get("X-RateLimit-Limit"));      // "30"
console.log(res.headers.get("X-RateLimit-Remaining"));  // "29"
console.log(res.headers.get("X-RateLimit-Reset"));      // "1699999999"
```

---

## 🚨 Error Handling

### Standar Error Response

```javascript
{
  success: false,
  data: null,
  meta: { timestamp: "..." },
  error: {
    code: "HTTP_405",
    message: "Method PUT tidak diizinkan...",
    status: 405,
    details: {}
  }
}
```

### Kode Error Umum

| Code | HTTP | Penyebab |
|------|------|----------|
| `HTTP_400` | 400 | Request salah |
| `HTTP_401` | 401 | Butuh login |
| `HTTP_403` | 403 | Tidak punya akses |
| `HTTP_404` | 404 | Endpoint/data tidak ada |
| `HTTP_405` | 405 | Method diblokir (PUT/DELETE/PATCH) |
| `HTTP_429` | 429 | Rate limit |
| `HTTP_500` | 500 | Internal error |
| `VALIDATION_ERROR` | 422 | Field request salah |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit |
| `ANIME_NOT_FOUND` | 404 | Slug anime tidak ada |
| `EPISODE_NOT_FOUND` | 404 | Episode tidak ada |
| `UPSTREAM_ERROR` | 502 | Server sumber error |
| `SCRAPE_ERROR` | 503 | Gagal scrape |

### Handler Global

```javascript
async function safeFetch(url, options = {}) {
  try {
    const res = await fetch(url, options);
    const json = await res.json();

    if (!json.success) {
      const err = new Error(json.error.message);
      err.code = json.error.code;
      err.status = json.error.status;
      err.details = json.error.details;
      throw err;
    }

    return json.data;
  } catch (err) {
    if (err.name === "TypeError") {
      // Network error
      console.error("Network error:", err.message);
      throw new Error("Tidak bisa konek ke API");
    }
    throw err;
  }
}

// Pakai
try {
  const data = await safeFetch("http://localhost:8000/share/anime/naruto");
  console.log(data.metadata.title);
} catch (err) {
  console.error(`[${err.code}] ${err.message}`);
}
```

---

## 🚫 Method Restriction

**Sejak v1.0.1**, API hanya terima **`GET`** & **`POST`**.

### Yang Diizinkan

| Method | Status |
|--------|--------|
| `GET` | ✅ |
| `POST` | ✅ |
| `OPTIONS` | ✅ (CORS preflight) |
| `HEAD` | ✅ (health check) |

### Yang Diblokir

| Method | Status |
|--------|--------|
| `PUT` | ❌ 405 |
| `DELETE` | ❌ 405 (kecuali `/keys/*`) |
| `PATCH` | ❌ 405 |

### Path Dikecualikan

- `/keys/*` — DELETE diizinkan (revoke API key)
- `/docs`, `/redoc`, `/openapi.json` — Swagger UI
- `/monitor` — monitoring dashboard

### Contoh Response 405

```javascript
const res = await fetch("http://localhost:8000/share/now", {
  method: "PUT",
});

console.log(res.status);   // 405
const json = await res.json();
console.log(json.error.code);      // "HTTP_405"
console.log(json.error.message);   // "Method PUT tidak diizinkan..."
console.log(res.headers.get("Allow")); // "GET, POST"
```

**Kalau frontend butuh PUT/DELETE:** Ubah ke `POST` atau tambahkan path ke `METHOD_EXCLUDED_PATHS` di `.env`.

---

## 🎯 Contoh Lengkap: Aplikasi Sederhana

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AniWatch Mini</title>
</head>
<body>
  <h1>AniWatch Mini</h1>
  <input id="keyword" placeholder="Cari anime...">
  <button onclick="doSearch()">Cari</button>
  <div id="results"></div>

  <script>
    const API = "http://localhost:8000";
    const API_KEY = "anw_xxxxxxxxxxxxx"; // Ganti dengan key kamu

    async function doSearch() {
      const keyword = document.getElementById("keyword").value.trim();
      if (!keyword) return;

      try {
        const res = await fetch(
          `${API}/share/query?q=${encodeURIComponent(keyword)}`,
          { headers: { "X-API-Key": API_KEY } }
        );
        const json = await res.json();

        if (!json.success) {
          throw new Error(json.error.message);
        }

        const results = json.data.results;
        document.getElementById("results").innerHTML = results
          .map((a) => `<div><b>${a.title}</b> — ${a.slug}</div>`)
          .join("");
      } catch (err) {
        document.getElementById("results").textContent = "Error: " + err.message;
      }
    }
  </script>
</body>
</html>
```

---

## 📝 Catatan

- Semua request **WAJIB** dari origin yang di-whitelist CORS
- Field di response di-baca dari `data.data.*` (bukan `data.*`)
- Untuk data anime: `data.data.metadata.*`
- Jangan lupa `credentials: "include"` kalau pakai cookie
- API key **hanya muncul sekali** saat dibuat

---

**©2026 Anicorporation.img**
**Developer:** Anikuze Ryuuzen
**Founder:** Lio Syberion