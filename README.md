# 🎌 AniWatch API

REST API untuk scraping anime dari Otakudesu, Kuramanime, AnimeIndo.

**Status:** ✅ Active · **Version:** 1.1.1 · **License:** Anicorporation.img License v1.0

---

## 📋 Daftar Isi

- [Fitur](#-fitur)
- [Tech Stack](#-tech-stack)
- [Instalasi](#-instalasi)
- [Konfigurasi](#-konfigurasi)
- [Menjalankan](#-menjalankan)
- [API Endpoints](#-api-endpoints)
- [Dokumentasi](#-dokumentasi)
- [Tools](#-tools)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Struktur Project](#-struktur-project)
- [License](#-license)

---

## ✨ Fitur

- 🎬 **Scraper Multi-Source** — Otakudesu (aktif), Kuramanime, AnimeIndo
- 🔒 **API Key Required** — Endpoint `/share/*` butuh API key
- 🚦 **Rate Limit** — Per API key, session, atau IP
- ⚡ **Cache 2-Tier** — Memory + file (persistent)
- 🚫 **Method Restriction** — Hanya `GET` & `POST`
- 🔐 **Multi-Auth** — API Key, Session Cookie, Bearer Token
- 🤖 **Auto Agent** — Scrape anime kosong di background
- 📊 **Monitoring** — Dashboard `/monitor`
- 🌐 **Web Portal** — `/portal` untuk manage API key
- 📚 **Dokumentasi** — Markdown di `/md`

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

## 🚀 Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/USERNAME/aniwatch.git
cd aniwatch
```

### 2. Buat Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment

```bash
# Copy dari example
copy .env.example .env

# Edit .env sesuai kebutuhan
notepad .env
```

### 5. Init Database

```bash
python -c "from db import init_db; init_db()"
```

---

## ⚙️ Konfigurasi

### `.env` Minimal

```env
# SOURCE
OTAKUDESU_ENABLED=true
OTAKUDESU_BASE_URL=https://otakudesu.blog
DEFAULT_SOURCE=otakudesu

# APP
APP_NAME=AniWatch API
DEBUG=false
LOG_LEVEL=INFO

# SERVER
HOST=0.0.0.0
PORT=8000

# DATABASE
DB_PATH=data/db/aniwatch.db

# API METHOD RESTRICTION
ALLOWED_METHODS=GET,POST
METHOD_EXCLUDED_PATHS=/keys,/docs,/redoc,/openapi.json,/monitor,/md

# CACHE
CACHE_ENABLED=true
CACHE_MEMORY_SIZE=1000
```

---

## 🏃 Menjalankan

### Development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

### Windows Shortcut

```cmd
start.bat
```

Server akan jalan di:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Monitor**: http://localhost:8000/monitor
- **Portal**: http://localhost:8000/portal
- **MD**: http://localhost:8000/md

---

## 📡 API Endpoints

### 🔓 Publik (Tanpa API Key)

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/` | Landing page |
| GET | `/health` | Health check |
| GET | `/stats` | Statistik DB |
| POST | `/login` | Login user |
| POST | `/register` | Register user |
| POST | `/get-key` | Generate API key |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |
| GET | `/monitor` | Monitoring dashboard |
| GET | `/md/*` | Dokumentasi markdown |

### 🔒 Terproteksi (Butuh API Key)

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/share/anime/{slug}` | Detail anime |
| GET | `/share/episodeid/{slug}` | List episode |
| GET | `/share/episode/{n}/{slug}` | Detail episode |
| GET | `/share/posterid/{slug}` | URL poster |
| GET | `/share/query?q=` | Search anime |
| GET | `/share/season/{season}` | Anime per season |
| GET | `/share/now` | Anime ongoing |
| POST | `/share/errorid/{slug}` | Report error |
| POST | `/share/empty/{slug}` | Force scrape |
| POST | `/share/linkask/{slug}` | Cek link |
| GET | `/share/scrape-status/{slug}` | Status scrape |
| GET | `/share/scrape-jobs` | List scrape jobs |

### 🔐 Auth

Semua request ke `/share/*` butuh header:
```http
X-API-Key: anw_xxxxxxxxxxxxx
```

---

## 📚 Dokumentasi

| File | Isi |
|------|-----|
| [`MD/usage.md`](MD/usage.md) | Panduan API (JavaScript) |
| [`MD/identity.md`](MD/identity.md) | Identitas project |
| [`MD/LICENSE.md`](MD/LICENSE.md) | Lisensi resmi |
| [`MD/copyright.md`](MD/copyright.md) | Copyright digital |
| [`MD/information.md`](MD/information.md) | Info teknis |
| [`MD/note.md`](MD/note.md) | Command reference |
| [`MD/CHANGELOG.md`](MD/CHANGELOG.md) | Riwayat versi |

---

## 🛠️ Tools

Semua tools di folder `tools/`:

```bash
# Manage API key
python tools/add_pass.py

# Monitor DB
python tools/db_monitor.py

# Scrape anime terbaru
python tools/scraper_update.py --limit 20

# Scrape by genre
python tools/scraper_by_genre.py --genre action --pages 5

# Analyze slug
python tools/analyzer_slug.py

# Scan bug
python tools/scanner.py --full

# Filter file sampah
python tools/filter.py --run

# Bersihkan
python tools/cleaner.py
```

Atau pakai menu interaktif:
```cmd
tools.bat
```

---

## 🧪 Testing

```bash
# Semua test
python -m pytest test/ -v

# Test API
python -m pytest test/test_api.py -v

# Test method restrictor
python -m pytest test/test_api.py::TestMethodRestrictor -v

# Test security
python -m pytest test/test_security.py -v
```

---

## 🌐 Deployment

### Local + ZROK Tunnel

```bash
# Terminal 1: Server
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: ZROK
zrok share reserved aniwatch
```

### Windows Service (Task Scheduler)

```cmd
cd agent
install_task.bat
```

Agent akan scrape ongoing tiap **6 jam** otomatis.

---

## 📁 Struktur Project

```
aniwatch/
├── main.py                    # Entry point FastAPI
├── config.py                  # Settings
├── requirements.txt           # Dependencies
├── start.bat                  # Launcher
├── tools.bat                  # Menu tools
├── .env.example               # Template config
├── README.md                  # File ini
│
├── api/                       # API layer
│   ├── middleware/            # Method restrictor + rate limit
│   ├── models/                # Pydantic schemas
│   ├── routes/                # Endpoints
│   ├── services/              # Business logic
│   ├── deps.py
│   └── exceptions.py
│
├── web/                       # Portal
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── detail.html
│   ├── license.html
│   ├── error/                 # Error pages
│   └── assets/
│
├── db/                        # Database layer
│   ├── database.py
│   ├── models.py
│   ├── repository.py
│   └── lock.py
│
├── security/                  # Auth
│   ├── api_key.py
│   ├── deps.py
│   ├── login.py
│   ├── password.py
│   ├── rate_limit.py
│   └── session.py
│
├── cache/                     # Cache layer
│   ├── memory.py
│   ├── file_cache.py
│   └── strategy.py
│
├── core/                      # Scraper
│   ├── fetcher.py
│   ├── extractors.py
│   ├── pipeline.py
│   └── sources/
│
├── agent/                     # Auto scraper
│   ├── runner.py
│   ├── cron.py
│   ├── scraper.py
│   └── config.py
│
├── control/                   # DB control
├── tools/                     # 15 tools
├── test/                      # Test suite
├── docs/                      # Monitoring HTML
├── MD/                        # Dokumentasi markdown
└── data/                      # DB + cache + logs
```

---

## 🔐 Security Notes

- ✅ API key untuk semua endpoint data
- ✅ Rate limit per key/IP
- ✅ Method restriction (GET/POST only)
- ✅ CORS whitelist
- ✅ Password hashing (SHA-256)
- ✅ Session management
- ✅ Input validation (Pydantic)

⚠️ **Untuk production:**
- Ganti password hashing ke **bcrypt/argon2**
- Pakai **HTTPS** (ZROK sudah handle)
- Migrate ke **PostgreSQL** kalau concurrent write tinggi
- Set `DEBUG=false`

---

## 📄 License

**Anicorporation.img License v1.0** — ©2026

Lihat [`MD/LICENSE.md`](MD/LICENSE.md) dan [`MD/copyright.md`](MD/copyright.md).

---

## 👥 Kontak

| Kanal | Info |
|-------|------|
| **Organisasi** | Anicorporation.img |
| **Developer** | [Anikuze Ryuuzen](https://github.com/USERNAME) |
| **Founder** | Lio Syberion |
| **Ex-Org** | SyberEco.corp.ind |
| **Ex-Founder** | Syres Alona |

---

## ⭐ Credits

- [Otakudesu](https://otakudesu.blog) — sumber data
- [FastAPI](https://fastapi.tiangolo.com/) — framework
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM

---

**©2026 Anicorporation.img — All Rights Reserved**
