"""
agent/cron.py - Internal scheduler (APScheduler).

Jalankan: python agent/cron.py

Ini akan jalan terus di background, scrape tiap INTERVAL_HOURS.
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
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    print("ERROR: APScheduler tidak terinstall")
    print("Install: pip install apscheduler")
    sys.exit(1)

from agent.config import get_config
from agent.runner import run, setup_logging


def main():
    cfg = get_config()

    # Setup logging
    log_dir = AGENT_DIR / cfg.log_dir
    log_path = setup_logging(
        log_dir, cfg.log_file, cfg.log_level,
        cfg.log_max_bytes, cfg.log_backup_count,
    )

    logger = logging.getLogger("agent.cron")
    logger.info("=" * 70)
    logger.info("  ANIWATCH AGENT - SCHEDULER")
    logger.info("=" * 70)
    logger.info(f"  Interval : {cfg.interval_hours} jam")
    logger.info(f"  Timezone : {cfg.timezone}")
    logger.info(f"  Log      : {log_path}")
    logger.info("=" * 70)

    scheduler = BlockingScheduler(timezone=cfg.timezone)

    # Job: scrape
    scheduler.add_job(
        lambda: run(skip_ongoing=False),
        trigger=IntervalTrigger(hours=cfg.interval_hours),
        id="scrape_job",
        name=f"Scrape setiap {cfg.interval_hours} jam",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(),  # jalankan langsung saat start
    )

    # Print jadwal
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