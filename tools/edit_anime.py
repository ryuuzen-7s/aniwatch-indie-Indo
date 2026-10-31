"""
edit_anime.py - Edit data anime di Database (Berdasarkan ID).

Alur:
1. Input ID Anime.
2. Tampilkan data lengkap.
3. Pilih field yang mau diedit.
4. Simpan.
"""
import sys
from pathlib import Path

# Path fix
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import select
from db import get_session
from db.models import Anime

# ─── COLORS ───
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"

def cprint(text, color=""):
    print(f"{color}{text}{C.RESET}")

def section(title):
    print()
    cprint("=" * 72, C.CYAN)
    cprint("  " + title, C.BOLD + C.CYAN)
    cprint("=" * 72, C.CYAN)


def display_anime(anime):
    """Tampilkan data lengkap anime."""
    section(f"DETAIL ANIME: {anime.title}")
    print(f"  [1] ID           : {anime.id}")
    print(f"  [2] Slug         : {anime.slug}")
    print(f"  [3] Judul (Title): {anime.title}")
    print(f"  [4] Judul JP     : {anime.title_jp or '-'}")
    print(f"  [5] Sinopsis     : {anime.synopsis[:100] + '...' if anime.synopsis else '-'}")
    print(f"  [6] Studio       : {anime.studio or '-'}")
    print(f"  [7] Status       : {anime.status or '-'}")
    print(f"  [8] Hari Tayang  : {anime.broadcast_day or '-'}")
    print(f"  [9] Total Episode: {anime.total_episode or '-'}")
    print(f"  [10] Rating      : {anime.rating or '-'}")
    print(f"  [11] Genre       : {', '.join(anime.genres) if anime.genres else '-'}")
    print(f"  [12] Poster URL  : {anime.poster_url or '-'}")
    print(f"  [0]  Batal / Kembali")


def edit_field(anime, s):
    """Proses edit field berdasarkan pilihan."""
    choice = input("\n  Pilih nomor field yang mau diedit (0-12): ").strip()

    if choice == "0":
        cprint("  ❌ Dibatalkan.", C.YELLOW)
        return

    try:
        if choice == "1":
            cprint("  ⚠️  ID tidak disarankan diubah (bisa merusak relasi).", C.YELLOW)
            return
        elif choice == "2":
            new_val = input(f"  Slug Baru [{anime.slug}]: ").strip()
            if new_val: anime.slug = new_val
        elif choice == "3":
            new_val = input(f"  Judul Baru [{anime.title}]: ").strip()
            if new_val: anime.title = new_val
        elif choice == "4":
            new_val = input(f"  Judul JP Baru [{anime.title_jp}]: ").strip()
            if new_val: anime.title_jp = new_val
        elif choice == "5":
            print(f"  Sinopsis saat ini: {anime.synopsis}")
            new_val = input("  Sinopsis Baru: ").strip()
            if new_val: anime.synopsis = new_val
        elif choice == "6":
            new_val = input(f"  Studio Baru [{anime.studio}]: ").strip()
            if new_val: anime.studio = new_val
        elif choice == "7":
            new_val = input(f"  Status Baru [{anime.status}]: ").strip()
            if new_val: anime.status = new_val
        elif choice == "8":
            new_val = input(f"  Hari Tayang Baru (Senin/dll) [{anime.broadcast_day}]: ").strip()
            if new_val: anime.broadcast_day = new_val
        elif choice == "9":
            cur = str(anime.total_episode) if anime.total_episode else "-"
            new_val = input(f"  Total Episode Baru [{cur}]: ").strip()
            if new_val:
                try:
                    anime.total_episode = int(new_val)
                except ValueError:
                    cprint("  ⚠️  Harus berupa angka. (Skip)", C.RED)
                    return
        elif choice == "10":
            cur = str(anime.rating) if anime.rating else "-"
            new_val = input(f"  Rating Baru [{cur}]: ").strip()
            if new_val:
                try:
                    anime.rating = float(new_val)
                except ValueError:
                    cprint("  ⚠️  Harus berupa angka desimal. (Skip)", C.RED)
                    return
        elif choice == "11":
            cur = ", ".join(anime.genres) if anime.genres else ""
            new_val = input(f"  Genre Baru (pisahkan koma) [{cur}]: ").strip()
            if new_val:
                anime.genres = [g.strip() for g in new_val.split(",") if g.strip()]
        elif choice == "12":
            new_val = input(f"  Poster URL Baru [{anime.poster_url}]: ").strip()
            if new_val: anime.poster_url = new_val
        else:
            cprint("  ❌ Pilihan tidak valid.", C.RED)
            return

        # Simpan ke DB
        s.commit()
        cprint(f"\n  ✅ Data berhasil disimpan!", C.GREEN)

    except Exception as e:
        s.rollback()
        cprint(f"\n  ❌ Gagal menyimpan: {e}", C.RED)


def main():
    while True:
        section("EDIT DATA ANIME (BY ID)")
        
        anime_id = input("  Masukkan ID Anime (atau ketik '0' untuk keluar): ").strip()
        
        if anime_id == "0" or anime_id == "":
            cprint("\n  👋 Bye!", C.CYAN)
            break
            
        if not anime_id.isdigit():
            cprint("  ❌ ID harus berupa angka.", C.RED)
            continue

        with get_session() as s:
            # Cari berdasarkan ID
            anime = s.execute(select(Anime).where(Anime.id == int(anime_id))).scalar_one_or_none()
            
            if not anime:
                cprint(f"  ❌ Anime dengan ID {anime_id} tidak ditemukan.", C.RED)
                input("\n  [Enter untuk lanjut]")
                continue

            # Tampilkan detail
            display_anime(anime)
            
            # Proses edit
            edit_field(anime, s)

        input("\n  [Enter untuk lanjut]")
        import os
        os.system("cls" if os.name == "nt" else "clear")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⏸️  Dibatalkan\n")