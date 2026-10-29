"""
get_slug.py - Extract slug dari JSON (Auto-Detect format).
"""
import sys
import re
import json
import argparse
from pathlib import Path
from dotenv import dotenv_values, set_key

# ─── PATH FIX ───
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
ROOT = _ROOT

# ─── CONFIG ───
BASE_DIR = ROOT / "data" / "base"
DUMP_DIR = BASE_DIR / "dump"
SLUGS_DIR = BASE_DIR / "slugs"
ENV_FILE = ROOT / "agent" / ".env"

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

# ─── AUTO FIND JSON ───
def find_best_json():
    """Cari file JSON terbaik secara otomatis."""
    # Prioritas 1: Slugs all
    p1 = SLUGS_DIR / "slugs_all.json"
    if p1.exists(): return p1
    
    # Prioritas 2: Dump
    p2 = DUMP_DIR / "slug_by_genre.json"
    if p2.exists(): return p2

    # Prioritas 3: File json pertama di folder slugs/
    if SLUGS_DIR.exists():
        for f in SLUGS_DIR.glob("*.json"):
            return f
            
    return None

# ─── EXTRACT SLUG (Support Format SLUG_N dan Nested) ───
def extract_slugs_from_file(path):
    if not path or not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        cprint(f"  ❌ Gagal baca {path.name}: {e}", C.RED)
        return []

    slugs = set()
    
    # Format 1: {"SLUG_1": "naruto", "SLUG_2": "bleach"}
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, str) and k.startswith("SLUG_"):
                slugs.add(v.strip())
                
    # Format 2: Nested {"action": {"animes": [{"slug": "naruto"}]}}
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and "animes" in v:
                for anime in v["animes"]:
                    if isinstance(anime, dict) and "slug" in anime:
                        slugs.add(anime["slug"].strip())

    # Format 3: Array [{"slug": "naruto"}, "bleach"]
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "slug" in item:
                slugs.add(item["slug"].strip())
            elif isinstance(item, str):
                slugs.add(item.strip())

    return list(slugs)

# ─── SAVE TO ENV ───
def save_to_env_format(slugs):
    """Simpan slug ke agent/.env (Max 20, Skip Duplikat, FIFO)."""
    if not ENV_FILE.exists():
        cprint(f"  ⚠️  File {ENV_FILE} tidak ada", C.YELLOW)
        return False

    raw = dotenv_values(ENV_FILE)
    
    # 1. Cek existing
    existing = []
    for key, val in raw.items():
        if key and key.startswith("SLUG_") and val:
            existing.append(val.strip())

    # 2. Filter duplikat
    to_add = []
    for slug in slugs:
        if slug not in existing and slug not in to_add:
            to_add.append(slug)

    if not to_add:
        cprint(f"  ℹ️  0 slug baru (semua sudah ada di .env)", C.YELLOW)
        return False

    # 3. Gabung & Batasi 20
    combined = existing + to_add
    if len(combined) > 20:
        combined = combined[-20:] # Ambil 20 terakhir

    # 4. Tulis ulang
    try:
        for i, slug in enumerate(combined, 1):
            set_key(ENV_FILE, f"SLUG_{i}", slug)
            
        # Hapus sisa SLUG_X lama jika sebelumnya ada >20
        for key in raw.keys():
            if key and key.startswith("SLUG_"):
                try:
                    num = int(key.split("_")[1])
                    if num > len(combined):
                        set_key(ENV_FILE, key, "")
                except ValueError:
                    pass
        return True
    except Exception as e:
        cprint(f"  ❌ Gagal: {e}", C.RED)
        return False

# ─── MENU INTERAKTIF ───
def interactive_menu():
    while True:
        target_json = find_best_json()
        
        section("🕷️  GET SLUG — Extract Slugs")
        print()
        print(f"  📁 File Input : {target_json.name if target_json else 'TIDAK DITEMUKAN'}")
        print(f"  ⚙️  Target Env : {ENV_FILE}")
        print()
        print("  [1] Simpan ke agent/.env (Max 20)")
        print("  [2] Cek isi JSON (Statistik)")
        print("  [0] Keluar")
        print()

        choice = input(f"  {C.CYAN}Pilih: {C.RESET}").strip()

        if choice == "0":
            cprint("\n  👋 Bye!", C.CYAN)
            break

        if not target_json:
            cprint("  ❌ Tidak ada file JSON di data/base/dump/ atau data/base/slugs/", C.RED)
            input("  [Enter]")
            continue

        slugs = extract_slugs_from_file(target_json)
        cprint(f"\n  🔍 Ditemukan {len(slugs)} slug unik di {target_json.name}", C.CYAN)

        if choice == "1":
            if save_to_env_format(slugs):
                cprint(f"\n  ✅ Slug baru berhasil disimpan ke agent/.env", C.GREEN)

        print()
        input(f"  {C.DIM}[Enter untuk lanjut]{C.RESET}")
        import os
        os.system("cls" if os.name == "nt" else "clear")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", action="store_true", help="Langsung simpan ke agent/.env (Headless)")
    args = ap.parse_args()

    if args.env:
        target_json = find_best_json()
        if not target_json:
            cprint("  ❌ Tidak ada file JSON ditemukan", C.RED)
            return
            
        slugs = extract_slugs_from_file(target_json)
        if save_to_env_format(slugs):
            cprint(f"  ✅ Slug berhasil disimpan ke agent/.env (Max 20)", C.GREEN)
        else:
            cprint(f"  ℹ️  Tidak ada slug baru untuk ditambahkan", C.YELLOW)
        return

    interactive_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⏸️  Interrupted\n")