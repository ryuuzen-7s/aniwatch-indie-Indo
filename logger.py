"""
Setup logging terpusat untuk Aniwatch.

Fitur:
  - Console handler (level INFO)
  - File handler dengan rotasi harian (7 hari)
  - Aman dipanggil berkali-kali (tidak duplikat handler)
  - Nama file log: data/log/aniwatch.log
"""
import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from config import config


def get_logger(name: str) -> logging.Logger:
    """
    Ambil logger dengan nama tertentu.

    Aman dipanggil berkali-kali dari modul berbeda —
    handler hanya dipasang sekali.
    """
    logger = logging.getLogger(name)

    if logger.handlers:  # sudah pernah di-setup
        return logger

    logger.setLevel(config.LOG_LEVEL)
    logger.propagate = False

    formatter = logging.Formatter(config.LOG_FORMAT)

    # ------------------------------------------------------------------
    # Console handler
    # ------------------------------------------------------------------
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # ------------------------------------------------------------------
    # File handler (rotasi harian, simpan 7 hari)
    # ------------------------------------------------------------------
    try:
        config.ensure_dirs()
        log_file = config.LOG_DIR / "aniwatch.log"
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            backupCount=7,
            encoding="utf-8",
            delay=True,
        )
        file_handler.setLevel(config.LOG_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as e:
        # Kalau folder tidak bisa ditulis, tetap jalan dengan console saja
        logger.warning(f"Tidak bisa menulis file log: {e}")

    return logger