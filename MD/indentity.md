# 🎌 AniWatch — Identity

> **Project:** AniWatch API
> **Organization:** Anicorporation.img
> **Developer:** Anikuze Ryuuzen
> **Version:** 1.5.0
> **Year:** ©2026

---

## 📌 Project Overview
**AniWatch** adalah REST API untuk scraping anime dari Otakudesu (dan soon Kuramanime, AnimeIndo). Dibangun dengan **FastAPI** + **SQLAlchemy** + **Pydantic v2** dengan arsitektur modern, dilengkapi dengan 3-mode auto-scraper agent.

### 🎯 Tujuan
- Menyediakan API bersih untuk data anime (metadata, episode, stream, download).
- Mendukung multiple source (multi-mirror).
- Cache 2-tier (memory + file) untuk performa tinggi.
- Rate limiting untuk mencegah abuse.
- Method restriction (GET & POST only) untuk keamanan.

### 🌐 Base URL
| Environment | URL |
|-------------|-----|
| **Local** | `http://localhost:8000` |
| **Public (ZROK)** | `https://aniwatch.share.zrok.io` |

---

## 🏢 Organization
| Aspek | Detail |
|-------|--------|
| **Nama** | Anicorporation.img |
| **Developer** | Anikuze Ryuuzen |
| **Pendiri** | Lio Syberion |
| **Tahun** | ©2026 |
| **Status** | Private Project |

### Tim Inti
| Nama | Peran |
|------|-------|
| **Anikuze Ryuuzen** | Lead Developer |
| **Lio Syberion** | Pendiri Organisasi |
| **Tia Yunia** | Anggota |

---

## 📜 Sejarah Organisasi
| Periode | Organisasi | Pendiri |
|---------|-----------|---------|
| Sebelum 2026 | **SyberEco.corp.ind** | Syres Alona |
| 2026 — Sekarang | **Anicorporation.img** | Lio Syberion |

**Serah terima:** 2026 — dari SyberEco.corp.ind ke Anicorporation.img (Detail lengkap di `04-copyright.md`).

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

**©2026 Anicorporation.img — All Rights Reserved**
