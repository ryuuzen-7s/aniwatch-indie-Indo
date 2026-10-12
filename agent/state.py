"""
agent/state.py — State sharing untuk agent modes.

Fitur:
- Track mode yang sedang aktif (idle / caller / follow_env)
- Track slug yang sedang di-scrape
- Track queue slug untuk caller
- Track follow_env paused status
- Pakai file JSON + thread lock

File: agent/state.json
"""
import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════
AGENT_DIR = Path(__file__).parent.resolve()
STATE_FILE = AGENT_DIR / "state.json"


# ═══════════════════════════════════════════════════════════
#  LOCK
# ═══════════════════════════════════════════════════════════
_STATE_LOCK = threading.RLock()


# ═══════════════════════════════════════════════════════════
#  DEFAULT STATE
# ═══════════════════════════════════════════════════════════
DEFAULT_STATE: Dict[str, Any] = {
    "mode": "idle",                 # "idle" | "caller" | "follow_env"
    "current_slug": None,
    "current_source": None,
    "started_at": None,
    "caller_queue": [],
    "follow_env_paused": False,
    "follow_env_paused_at": None,
    "last_caller_at": None,
    "last_follow_env_at": None,
    "stats": {
        "caller_total": 0,
        "caller_success": 0,
        "caller_failed": 0,
        "follow_env_total": 0,
        "follow_env_success": 0,
        "follow_env_failed": 0,
    },
}


# ═══════════════════════════════════════════════════════════
#  READ / WRITE
# ═══════════════════════════════════════════════════════════
def read_state() -> Dict[str, Any]:
    """Baca state dari file. Return default kalau tidak ada."""
    with _STATE_LOCK:
        if not STATE_FILE.exists():
            return DEFAULT_STATE.copy()

        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            merged = DEFAULT_STATE.copy()
            merged.update(data)
            # Merge stats (kalau ada field baru)
            if "stats" in data:
                merged["stats"] = {**DEFAULT_STATE["stats"], **data["stats"]}
            return merged
        except Exception as e:
            logger.warning(f"[State] Gagal baca: {e}")
            return DEFAULT_STATE.copy()


def write_state(state: Dict[str, Any]) -> None:
    """Tulis state ke file."""
    with _STATE_LOCK:
        try:
            STATE_FILE.write_text(
                json.dumps(state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"[State] Gagal tulis: {e}")


def update_state(**kwargs) -> Dict[str, Any]:
    """Update state dengan field baru."""
    with _STATE_LOCK:
        state = read_state()
        state.update(kwargs)
        write_state(state)
        return state


# ═══════════════════════════════════════════════════════════
#  MODE HELPERS
# ═══════════════════════════════════════════════════════════
def set_mode(mode: str) -> None:
    """Set mode: idle / caller / follow_env."""
    update_state(mode=mode)


def get_mode() -> str:
    """Get mode sekarang."""
    return read_state().get("mode", "idle")


def is_busy() -> bool:
    """Cek apakah agent sibuk."""
    return get_mode() != "idle"


def is_caller_running() -> bool:
    return get_mode() == "caller"


def is_follow_env_running() -> bool:
    return get_mode() == "follow_env"


# ═══════════════════════════════════════════════════════════
#  FOLLOW_ENV PAUSE / RESUME
# ═══════════════════════════════════════════════════════════
def pause_follow_env() -> bool:
    """Pause follow_env mode."""
    state = read_state()
    if state.get("follow_env_paused"):
        return False

    update_state(
        follow_env_paused=True,
        follow_env_paused_at=datetime.now(timezone.utc).isoformat(),
    )
    logger.info("[State] follow_env PAUSED")
    return True


def resume_follow_env() -> bool:
    """Resume follow_env mode."""
    state = read_state()
    if not state.get("follow_env_paused"):
        return False

    update_state(
        follow_env_paused=False,
        follow_env_paused_at=None,
    )
    logger.info("[State] follow_env RESUMED")
    return True


def is_follow_env_paused() -> bool:
    return read_state().get("follow_env_paused", False)


# ═══════════════════════════════════════════════════════════
#  CALLER QUEUE
# ═══════════════════════════════════════════════════════════
def push_caller_slug(slug: str, source: str = "otakudesu") -> int:
    """Tambah slug ke queue caller. Return posisi (0-based), -1 kalau duplikat."""
    state = read_state()
    queue = state.get("caller_queue", [])

    if any(item["slug"] == slug for item in queue):
        return -1

    queue.append({
        "slug": slug,
        "source": source,
        "queued_at": datetime.now(timezone.utc).isoformat(),
    })
    update_state(
        caller_queue=queue,
        last_caller_at=datetime.now(timezone.utc).isoformat(),
    )
    return len(queue) - 1


def pop_caller_slug() -> Optional[Dict[str, Any]]:
    """Ambil slug dari queue (FIFO)."""
    state = read_state()
    queue = state.get("caller_queue", [])

    if not queue:
        return None

    item = queue.pop(0)
    update_state(caller_queue=queue)
    return item


def get_caller_queue() -> List[Dict[str, Any]]:
    return read_state().get("caller_queue", [])


def clear_caller_queue() -> int:
    state = read_state()
    count = len(state.get("caller_queue", []))
    update_state(caller_queue=[])
    return count


# ═══════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════
def increment_stat(key: str, delta: int = 1) -> None:
    state = read_state()
    stats = state.get("stats", {})
    stats[key] = stats.get(key, 0) + delta
    update_state(stats=stats)


def get_stats() -> Dict[str, int]:
    return read_state().get("stats", {})


def reset_stats() -> None:
    update_state(stats=DEFAULT_STATE["stats"].copy())


# ═══════════════════════════════════════════════════════════
#  CURRENT SCRAPE
# ═══════════════════════════════════════════════════════════
def set_current(slug: str, source: str = "otakudesu") -> None:
    update_state(
        current_slug=slug,
        current_source=source,
        started_at=datetime.now(timezone.utc).isoformat(),
    )


def clear_current() -> None:
    update_state(current_slug=None, current_source=None, started_at=None)


def get_current() -> Optional[Dict[str, Any]]:
    state = read_state()
    if not state.get("current_slug"):
        return None
    return {
        "slug": state["current_slug"],
        "source": state.get("current_source"),
        "started_at": state.get("started_at"),
    }


# ═══════════════════════════════════════════════════════════
#  FULL STATE
# ═══════════════════════════════════════════════════════════
def get_full_state() -> Dict[str, Any]:
    return read_state()


def reset_state() -> None:
    write_state(DEFAULT_STATE.copy())
    logger.info("[State] Reset ke default")