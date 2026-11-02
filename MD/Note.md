# 📝 AniWatch — Developer Reference

Panduan referensi cepat untuk Git Workflow dan Command Line AniWatch API.

---

## 📋 1. Git & Release Workflow

### Daily Commit (Conventional Commits)
```cmd
git add .
git commit -m "feat: tambah fitur pagination"
git push origin main
```

Format Prefix: feat:, fix:, docs:, refactor:, chore:, perf:.

Rilis Versi Baru

1. Update config.py (app_version = "1.5.0").
2. Update MD/CHANGELOG.md.
3. Commit: git commit -m "chore: bump version to v1.5.0"
4. Tag & Push:
   ```cmd
   git tag -a v1.5.0 -m "Release v1.5.0"
   git push origin main
   git push origin v1.5.0
   ```

(GitHub Actions akan otomatis membuat Release).

---

🚀 2. Running Server & ZROK

Mode Production (Hemat RAM)

```cmd
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
```

Atau pakai script: start.bat

Tunnel ZROK (Terminal Baru)

```cmd
zrok share reserved aniwatch
```

---

🤖 3. Agent Scraper (3 Mode)

Mode 1: Hybrid (Recommended)

Menjalankan follow_env di background, tapi langsung memotong proses jika ada caller masuk.

```cmd
python agent\coordinator.py --watch --interval 60
```

Mode 2: Follow .env (Sekali Jalan)

Scrape semua slug dari agent/.env + auto ongoing.

```cmd
python agent\runner.py
```

Mode 3: Agent Caller (Scrape 1 Anime)

Memaksa scrape 1 anime spesifik saat itu juga.

```cmd
python agent\caller.py naruto-sub-indo
```

Task Scheduler (Windows)

Daftarkan agent agar jalan otomatis tiap 12 jam (buka CMD as Administrator):

```cmd
cd /d A:\aniwatch\agent
install_task.bat
```

---

🛠️ 4. Tools & Monitoring

Semua command dijalankan dari root folder.

Command Fungsi
python tools\db_monitor.py Monitoring DB
python tools\add_pass.py Manage API Key
python tools\scraper_update.py --limit 10 Scrape manual 10 anime
python tools\scanner.py Scan bug di kode
python tools\filter.py --run Bersihkan file sampah
tools.bat Menu interaktif semua tools

---

🧪 5. Testing

```cmd
:: Semua test
python -m pytest test\ -v

:: Test API & Method Restrictor
python -m pytest test\test_api.py -v
```

---

🌐 6. Akses Web Portal

Halaman URL
Portal http://localhost:8000/portal
Swagger UI http://localhost:8000/docs
Monitoring http://localhost:8000/monitor

---

🚨 7. Troubleshooting

Masalah Solusi
Database is locked Matikan terminal agent. Restart server.
Error 429 (Rate Limit) Tunggu 1 menit.
Error 404 di Portal Akses /portal (tanpa /index.html).
Agent tidak jalan otomatis CMD Admin: schtasks /Run /TN "AniWatchAgent"

```

---

Semua isi di atas sudah **100% sinkron** dengan kode v1.5.0 yang baru kita perbaiki (termasuk `broadcast_day` dan path `/portal`). Kamu tinggal *copy-paste* ke masing-masing file di folder `MD/`.
