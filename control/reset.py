"""
control/reset.py — Reset database.

Jalankan:
    python -m control.reset --confirm       # reset penuh (butuh konfirmasi)
    python -m control.reset --drop          # hapus semua tabel
    python -m control.reset --recreate      # drop + create ulang
"""
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from db import init_db, reset_db, engine
from db.models import Base


def drop_all():
    print("  ⚠️  Dropping semua tabel...")
    Base.metadata.drop_all(bind=engine)
    print("  ✅ Dropped")


def recreate():
    print("  🔄 Recreate tabel...")
    reset_db()
    print("  ✅ Recreated")


def main():
    args = sys.argv[1:]

    print("=" * 62)
    print("  ⚠️  DATABASE RESET")
    print("=" * 62)

    if "--drop" in args:
        drop_all()
    elif "--recreate" in args:
        recreate()
    elif "--confirm" in args:
        print("  🔴 SEMUA DATA AKAN DIHAPUS!")
        confirm = input("  Ketik 'RESET' untuk konfirmasi: ").strip()
        if confirm == "RESET":
            recreate()
        else:
            print("  ❌ Dibatalkan")
    else:
        print("  Usage:")
        print("    python -m control.reset --drop")
        print("    python -m control.reset --recreate")
        print("    python -m control.reset --confirm")


if __name__ == "__main__":
    main()