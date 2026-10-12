"""
agent/logger.py — Setup logging untuk agent modes.
"""
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_agent_logging(
    log_dir: Path,
    log_file: str,
    level: str = "INFO",
    max_bytes: int = 5_242_880,
    backup_count: int = 5,
) -> Path:
    """
    Setup logging dengan rotasi file.

    Returns:
        Path log file.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Hapus handler lama
    root.handlers.clear()

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    root.addHandler(console)

    # File handler
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    root.addHandler(file_handler)

    return log_path