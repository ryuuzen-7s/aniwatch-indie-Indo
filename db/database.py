"""
db/database.py — Koneksi SQLite + session management.

Fitur hardening:
- WAL mode (concurrent read/write)
- Foreign key ON
- Busy timeout 60s
- Auto-checkpoint WAL
- Session per-request
- Auto-create tabel
"""
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from config import settings


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  ENGINE
# ═══════════════════════════════════════════════════════════
# Pastikan folder ada
settings.db_full_path.parent.mkdir(parents=True, exist_ok=True)

# URL: sqlite:///path/ke/db.sqlite
DATABASE_URL = f"sqlite:///{settings.db_full_path}"

engine: Engine = create_engine(
    DATABASE_URL,
    echo=settings.db_echo,
    # Concurrent access dari threadpool FastAPI
    connect_args={
        "check_same_thread": False,
        "timeout": 60,              # ← 60 detik (dari 30)
    },
    # Connection pool
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)


# ═══════════════════════════════════════════════════════════
#  PRAGMA (SQLite optimizations)
# ═══════════════════════════════════════════════════════════
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, conn_record):
    """Set PRAGMA setiap koneksi baru."""
    cursor = dbapi_conn.cursor()
    try:
        # Foreign key ON (default OFF di SQLite!)
        cursor.execute("PRAGMA foreign_keys=ON")
        # WAL mode → concurrent read/write
        cursor.execute("PRAGMA journal_mode=WAL")
        # Synchronous NORMAL → lebih cepat, masih aman
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Cache 64MB
        cursor.execute("PRAGMA cache_size=-64000")
        # Busy timeout 60s (dari 30s)
        cursor.execute("PRAGMA busy_timeout=60000")
        # Auto-checkpoint WAL (truncate file)
        cursor.execute("PRAGMA wal_autocheckpoint=1000")
        # Temp store di memory
        cursor.execute("PRAGMA temp_store=MEMORY")
    except Exception as e:
        logger.warning(f"PRAGMA setup error: {e}")
    finally:
        cursor.close()


# ═══════════════════════════════════════════════════════════
#  SESSION
# ═══════════════════════════════════════════════════════════
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # biar object bisa diakses setelah commit
    class_=Session,
    future=True,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager untuk session.

    Usage:
        with get_session() as session:
            anime = session.query(Anime).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency untuk FastAPI.

    Usage:
        @app.get("/anime/{slug}")
        def get_anime(slug: str, db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  INIT / RESET
# ═══════════════════════════════════════════════════════════
def init_db() -> None:
    """Buat semua tabel (kalau belum ada)."""
    from .models import Base

    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"✅ Database initialized: {settings.db_full_path}")
    except Exception as e:
        logger.error(f"❌ init_db error: {e}")
        raise


def reset_db() -> None:
    """HAPUS semua tabel + buat ulang. ⚠️ Data hilang!"""
    from .models import Base

    logger.warning("⚠️  reset_db: menghapus semua tabel!")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database reset selesai")


def db_info() -> dict:
    """Info DB untuk debug."""
    with engine.connect() as conn:
        tables = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()
        size = settings.db_full_path.stat().st_size if settings.db_full_path.exists() else 0

    return {
        "path": str(settings.db_full_path),
        "size_kb": round(size / 1024, 2),
        "tables": [t[0] for t in tables],
        "wal_mode": _check_wal_mode(),
    }


def _check_wal_mode() -> bool:
    """Cek apakah WAL mode aktif."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA journal_mode")).fetchone()
            return result and result[0].lower() == "wal"
    except Exception:
        return False


def checkpoint_wal() -> dict:
    """
    Checkpoint WAL untuk truncate file.
    Berguna kalau file .db-wal membesar.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)")).fetchone()
            return {
                "success": True,
                "busy": result[0] if result else 0,
                "log_pages": result[1] if result else 0,
                "checkpointed": result[2] if result else 0,
            }
    except Exception as e:
        logger.error(f"Checkpoint error: {e}")
        return {"success": False, "error": str(e)}


def vacuum_db() -> dict:
    """VACUUM DB untuk compact."""
    try:
        with engine.connect() as conn:
            conn.execute(text("VACUUM"))
        return {"success": True}
    except Exception as e:
        logger.error(f"Vacuum error: {e}")
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════
#  QUICK TEST
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Path fix
    if __package__ is None:
        sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    print("=" * 62)
    print("  DATABASE TEST")
    print("=" * 62)

    # Init
    init_db()

    # Info
    info = db_info()
    print(f"\n📁 Path     : {info['path']}")
    print(f"📏 Size     : {info['size_kb']} KB")
    print(f"📋 Tables   : {info['tables']}")
    print(f"🔧 WAL mode : {info['wal_mode']}")

    # Test session
    print("\n🧪 Test session...")
    with get_session() as session:
        result = session.execute(text("SELECT 1")).fetchone()
        print(f"   Query result: {result}")

    # Test checkpoint
    print("\n🧪 Test checkpoint WAL...")
    cp = checkpoint_wal()
    print(f"   Checkpoint: {cp}")

    print("\n" + "=" * 62)
    print("  ✅ DB OK")
    print("=" * 62)