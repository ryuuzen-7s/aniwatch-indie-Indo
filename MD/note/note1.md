# 🚀 Panduan Commit & Release — AniWatch API

Dokumen ini berisi referensi cepat (cheat sheet) untuk menyimpan perubahan (commit), mengunggah ke GitHub (push), dan merilis versi baru (release) menggunakan GitHub Actions.

---

## 📋 1. Alur Kerja Standar (Daily Commit)

Gunakan alur ini setiap kali kamu selesai mengedit kode (API, Database, Agent, dll) atau memperbarui dokumentasi.

### Langkah 1: Cek Status
Lihat file apa saja yang berubah.
```cmd
git status
```

### Langkah 2: Tambahkan File
Tambahkan semua file yang berubah ke *staging area*.
```cmd
git add .
```

### Langkah 3: Commit
Simpan perubahan dengan pesan yang jelas (gunakan format *Conventional Commits*).
```cmd
git commit -m "feat: tambah fitur pagination"
```
*(Lihat panduan format pesan di bagian bawah).*

### Langkah 4: Push ke GitHub
Kirim perubahan dari laptop ke repository GitHub.
```cmd
git push origin main
```

---

## 🏷️ 2. Rilis Versi Baru (Release)

Jika perubahan yang kamu lakukan sudah stabil dan siap dirilis sebagai versi baru (misal dari `v1.3.0` ke `v1.4.0`), ikuti langkah ini.

### Langkah 1: Update Versi
1. Buka `config.py`, ubah `app_version = "1.4.0"`.
2. Buka `MD/CHANGELOG.md`, tambahkan catatan rilis untuk versi `1.4.0`.
3. (Opsional) Buka `README.md`, update *badge* versi.

### Langkah 2: Commit Perubahan Versi
```cmd
git add .
git commit -m "chore: bump version to v1.4.0"
git push origin main
```

### Langkah 3: Buat Tag Git
Tag ini yang akan memicu robot GitHub Actions untuk membuat halaman *Release* secara otomatis.
```cmd
git tag -a v1.4.0 -m "Manual Data Editor & Sinkronisasi"
```

### Langkah 4: Push Tag
```cmd
git push origin v1.4.0
```

### Langkah 5: Pantau GitHub Actions
1. Buka repository GitHub kamu di browser.
2. Klik tab **Actions**.
3. Tunggu sampai proses **"Auto Release & Changelog"** selesai (berwarna hijau).
4. Buka tab **Releases** untuk melihat hasilnya.

---

## 📝 3. Format Pesan Commit (Conventional Commits)

Gunakan awalan (prefix) berikut agar riwayat commit rapi dan mudah dipahami:

| Prefix | Kapan Digunakan | Contoh |
|--------|-----------------|--------|
| `feat:` | Menambah fitur baru | `feat: add endpoint jadwal harian` |
| `fix:` | Memperbaiki bug | `fix: perbaiki error database locked` |
| `docs:` | Mengubah dokumentasi | `docs: update usage.md untuk pagination` |
| `refactor:` | Mengubah struktur kode (tanpa ubah fitur) | `refactor: pisahkan service now dan day` |
| `chore:` | Tugas rutin (update versi, config) | `chore: bump version to v1.4.0` |
| `perf:` | Meningkatkan performa | `perf: tambah GZip Middleware` |
| `style:` | Format kode (spasi, indentasi) | `style: rapikan import` |

---

## ⚠️ 4. Jika Terjadi Kesalahan

### Lupa Menambahkan File di Commit Terakhir
```cmd
git add file_yang_lupa.py
git commit --amend --no-edit
```

### Salah Ketik Pesan Commit
```cmd
git commit --amend -m "pesan commit yang benar"
```

### Ingin Membatalkan Commit (Belum di-Push)
```cmd
git reset --soft HEAD~1
```
*(File yang di-commit akan kembali ke staging area).*

### Salah Membuat Tag
```cmd
:: Hapus tag lokal
git tag -d v1.4.0

:: Hapus tag di GitHub
git push origin :refs/tags/v1.4.0
```

### Konflik Git (Conflict)
Jika ada tulisan `CONFLICT` saat melakukan `git pull` atau `git push`:
1. Buka file yang konflik.
2. Cari tanda `<<<<<<<`, `=======`, `>>>>>>>`.
3. Pilih kode mana yang ingin dipertahankan (hapus tanda-tandanya).
4. Jalankan `git add .` lalu `git commit`.

---

## 🧹 5. Pemeliharaan Repo

### Menghapus File yang Sudah Terlanjur di-Commit
Jika kamu tidak sengaja memasukkan file `.env` atau `.db` ke Git:
```cmd
git rm --cached .env
git rm --cached data/db/aniwatch.db
git commit -m "chore: remove sensitive files from tracking"
```

### Melihat Log Commit
```cmd
:: Melihat 5 commit terakhir secara ringkas
git log --oneline -5
```

---
**©2026 Anicorporation.img**