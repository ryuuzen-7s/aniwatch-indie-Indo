"""control — Panel kontrol database AniWatch."""
import os
import sys


def check_api_running() -> bool:
    """
    Cek apakah API (uvicorn) sedang jalan.
    Return True kalau ada proses uvicorn / port 8000 aktif.
    """
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(("127.0.0.1", 8000))
        s.close()
        return result == 0  # 0 = port terbuka
    except Exception:
        return False


def warn_if_api_running():
    """Print warning kalau API sedang jalan."""
    if check_api_running():
        print()
        print("\033[93m" + "=" * 62 + "\033[0m")
        print("\033[93m  ⚠️  PERINGATAN: API sedang jalan di port 8000!\033[0m")
        print("\033[93m  Operasi tulis DB bisa gagal (database is locked).\033[0m")
        print("\033[93m  Solusi: Stop uvicorn dulu (Ctrl+C)\033[0m")
        print("\033[93m" + "=" * 62 + "\033[0m")
        print()
        return True
    return False