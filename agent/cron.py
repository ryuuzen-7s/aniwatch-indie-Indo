"""
agent/cron.py — Scheduler (APScheduler) untuk hybrid mode.

Jalankan: python agent/cron.py
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

# Path fix
ROOT = Path(__file__).parent.parent.resolve()
AGENT_DIR = Path(__file__).parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger
except ImportError:
    print("ERROR: APScheduler tidak terinstall")
    print("Install: pip install apscheduler")
    sys.exit(1)

from agent.config import get_config
from agent.coordinator import run_hybrid
from agent.logger import setup_agent_logging


def main():
    cfg = get_config()

    log_dir = AGENT_DIR / cfg.log_dir
    log_path = setup_agent_logging(
        log_dir, "cron.log", cfg.log_level,
        cfg.log_max_bytes, cfg.log_backup_count,
    )

    logger = logging.getLogger("agent.cron")
    logger.info("=" * 70)
    logger.info("  ANIWATCH AGENT - SCHEDULER (HYBRID MODE)")
    logger.info("=" * 70)
    logger.info(f"  Interval : {cfg.interval_hours} jam")
    logger.info(f"  Timezone : {cfg.timezone}")
    logger.info(f"  Mode     : {cfg.mode}")
    logger.info(f"  Log      : {log_path}")
    logger.info("=" * 70)

    scheduler = BlockingScheduler(timezone=cfg.timezone)

    scheduler.add_job(
        lambda: run_hybrid(skip_ongoing=False),
        trigger=IntervalTrigger(hours=cfg.interval_hours),
        id="hybrid_job",
        name=f"Hybrid scrape setiap {cfg.interval_hours} jam",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(),
    )

    for job in scheduler.get_jobs():
        logger.info(f"  Job: {job.name}")
        logger.info(f"  Next: {job.next_run_time}")

    logger.info("=" * 70)
    logger.info("  Tekan Ctrl+C untuk stop")
    logger.info("=" * 70)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")


if __name__ == "__main__":
    main()