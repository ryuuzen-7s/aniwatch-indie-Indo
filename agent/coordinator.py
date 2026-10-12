"""
agent/coordinator.py — Opsi 3: Hybrid mode.

Koordinator prioritas:
1. Cek caller queue → process (prioritas tinggi)
2. Kalau tidak ada → jalankan follow_env
3. Kalau caller masuk saat follow_env jalan:
   → pause follow_env, process caller, resume

Jalankan:
    python agent/coordinator.py              # sekali
    python agent/coordinator.py --watch      # watcher (default interval 60s)
    python agent/coordinator.py --watch --interval 30
"""
import sys
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Path fix
ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

AGENT_DIR = Path(__file__).parent.resolve()
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from agent.config import get_config
from agent import state
from agent.caller import run_caller, process_queue
from agent.runner import run as run_follow_env
from agent.logger import setup_agent_logging


logger = logging.getLogger("agent.coordinator")


# ═══════════════════════════════════════════════════════════
#  CHECK QUEUE
# ═══════════════════════════════════════════════════════════
def has_caller_queue() -> bool:
    return len(state.get_caller_queue()) > 0


# ═══════════════════════════════════════════════════════════
#  HYBRID — SEKALI JALAN
# ═══════════════════════════════════════════════════════════
def run_hybrid(skip_ongoing: bool = False) -> None:
    """
    Mode hybrid — auto switch antara caller & follow_env.
    """
    logger.info("=" * 70)
    logger.info("  AGENT COORDINATOR — HYBRID MODE")
    logger.info("=" * 70)
    logger.info(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    # ─── Step 1: Cek queue dulu ───
    if has_caller_queue():
        logger.info("[Coordinator] Step 1: Process caller queue")
        process_queue()

    # ─── Step 2: Jalankan follow_env ───
    logger.info("[Coordinator] Step 2: Process follow_env")
    state.set_mode("follow_env")
    state.increment_stat("follow_env_total")

    try:
        run_follow_env(skip_ongoing=skip_ongoing)
        state.increment_stat("follow_env_success")
    except Exception as e:
        logger.error(f"[Coordinator] follow_env gagal: {e}")
        state.increment_stat("follow_env_failed")
    finally:
        state.set_mode("idle")
        state.update_state(
            last_follow_env_at=datetime.now(timezone.utc).isoformat(),
        )

    logger.info("[Coordinator] Selesai")


# ═══════════════════════════════════════════════════════════
#  WATCHER — auto cek queue tiap N detik
# ═══════════════════════════════════════════════════════════
def run_watcher(interval: int = 60) -> None:
    """
    Watcher mode — cek caller queue tiap N detik.
    """
    logger.info("=" * 70)
    logger.info("  AGENT COORDINATOR — WATCHER MODE")
    logger.info("=" * 70)
    logger.info(f"  Interval: {interval}s")
    logger.info(f"  Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    try:
        while True:
            # ─── Cek caller queue ───
            if has_caller_queue():
                logger.info("[Coordinator] Queue detected, processing...")
                process_queue()

            # ─── Sleep ───
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("[Coordinator] Watcher stopped by user")
    except Exception as e:
        logger.exception(f"[Coordinator] Watcher error: {e}")


# ═══════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="Agent Coordinator (Hybrid Mode)")
    ap.add_argument("--once", action="store_true", help="Sekali jalan")
    ap.add_argument("--watch", action="store_true", help="Watcher mode")
    ap.add_argument("--interval", type=int, default=60, help="Watcher interval (default 60s)")
    ap.add_argument("--skip-ongoing", action="store_true")
    args = ap.parse_args()

    cfg = get_config()
    log_dir = AGENT_DIR / cfg.log_dir
    setup_agent_logging(
        log_dir, "coordinator.log", cfg.log_level,
        cfg.log_max_bytes, cfg.log_backup_count,
    )

    if args.watch:
        run_watcher(interval=args.interval)
    else:
        run_hybrid(skip_ongoing=args.skip_ongoing)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n[Coordinator] Interrupted by user")
    except Exception as e:
        logger.exception(f"[Coordinator] Fatal error: {e}")