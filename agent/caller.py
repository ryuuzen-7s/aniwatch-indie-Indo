"""
agent/caller.py — Opsi 1: Agent Caller mode.

Scrape 1 slug yang dipanggil. Kalau follow_env sedang jalan,
pause dulu, resume setelah selesai.

Jalankan:
    python agent/caller.py <slug>
    python agent/caller.py <slug> --source otakudesu
    python agent/caller.py --queue          # proses queue
    python agent/caller.py --status         # status
    python agent/caller.py --push <slug>    # push ke queue
"""
import sys
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Path fix
ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

AGENT_DIR = Path(__file__).parent.resolve()
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from agent.config import get_config
from agent.scraper import scrape_one
from agent import state
from agent.logger import setup_agent_logging


logger = logging.getLogger("agent.caller")


# ═══════════════════════════════════════════════════════════
#  CALLER MODE
# ═══════════════════════════════════════════════════════════
def run_caller(slug: str, source: str = "otakudesu") -> dict:
    """
    Jalankan caller mode untuk 1 slug.
    """
    follow_env_was_paused = False

    # ─── Cek follow_env ───
    if state.is_follow_env_running():
        logger.info("[Caller] follow_env sedang jalan, pause dulu...")
        state.pause_follow_env()
        follow_env_was_paused = True

        wait_start = time.time()
        while state.is_follow_env_running() and time.time() - wait_start < 30:
            time.sleep(0.5)

        if state.is_follow_env_running():
            logger.warning("[Caller] follow_env tidak pause, lanjut paksa...")
        else:
            logger.info("[Caller] follow_env paused ✅")

    # ─── Set mode ───
    state.set_mode("caller")
    state.set_current(slug, source)
    state.increment_stat("caller_total")

    # ─── Header ───
    logger.info("=" * 70)
    logger.info(f"  AGENT CALLER — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    logger.info(f"  Slug   : {slug}")
    logger.info(f"  Source : {source}")
    logger.info(f"  Mode   : CALLER (prioritas tinggi)")
    if follow_env_was_paused:
        logger.info(f"  Info   : follow_env paused sementara")
    logger.info("=" * 70)

    # ─── Scrape ───
    t0 = time.time()
    try:
        result = scrape_one(slug, follow_all=True, skip_existing=False)
    except Exception as e:
        logger.exception(f"[Caller] Error: {e}")
        result = {"status": "error", "error": str(e), "duration": 0}

    duration = time.time() - t0

    # ─── Result ───
    if result.get("status") == "ok":
        c = result.get("counters", {})
        logger.info(
            f"  ✅ SUKSES ({duration:.1f}s) — "
            f"{c.get('anime', 0)} anime, {c.get('episodes', 0)} ep, "
            f"{c.get('downloads', 0)} dl"
        )
        state.increment_stat("caller_success")
    else:
        logger.error(f"  ❌ GAGAL ({duration:.1f}s) — {result.get('error')}")
        state.increment_stat("caller_failed")

    # ─── Clear ───
    state.clear_current()
    state.set_mode("idle")

    # ─── Resume follow_env ───
    if follow_env_was_paused:
        logger.info("[Caller] Resume follow_env...")
        state.resume_follow_env()

    logger.info("=" * 70)
    return result


# ═══════════════════════════════════════════════════════════
#  PROCESS QUEUE
# ═══════════════════════════════════════════════════════════
def process_queue() -> None:
    """Proses semua slug di queue."""
    queue = state.get_caller_queue()

    if not queue:
        logger.info("[Caller] Queue kosong")
        return

    logger.info(f"[Caller] Process queue: {len(queue)} slug")

    for i, item in enumerate(queue, 1):
        slug = item["slug"]
        source = item.get("source", "otakudesu")

        logger.info(f"[Caller] [{i}/{len(queue)}] {slug}")

        state.pop_caller_slug()

        try:
            run_caller(slug, source=source)
        except Exception as e:
            logger.error(f"[Caller] Gagal {slug}: {e}")

        if i < len(queue):
            time.sleep(2)

    logger.info(f"[Caller] Queue selesai")


# ═══════════════════════════════════════════════════════════
#  STATUS
# ═══════════════════════════════════════════════════════════
def display_status() -> None:
    s = state.get_full_state()

    print()
    print("=" * 70)
    print("  AGENT STATUS")
    print("=" * 70)
    print(f"  Mode              : {s.get('mode', 'idle')}")
    print(f"  Current slug      : {s.get('current_slug') or '-'}")
    print(f"  Current source    : {s.get('current_source') or '-'}")
    print(f"  Started at        : {s.get('started_at') or '-'}")
    print(f"  Follow_env paused : {s.get('follow_env_paused', False)}")
    print()
    print(f"  Caller queue      : {len(s.get('caller_queue', []))} slug")
    for i, item in enumerate(s.get("caller_queue", []), 1):
        print(f"    [{i}] {item['slug']} ({item.get('source', '-')})")
    print()
    print(f"  Last caller       : {s.get('last_caller_at') or '-'}")
    print(f"  Last follow_env   : {s.get('last_follow_env_at') or '-'}")
    print()
    print("  Stats:")
    stats = s.get("stats", {})
    print(f"    Caller     : {stats.get('caller_total', 0)} total, "
          f"{stats.get('caller_success', 0)} ok, "
          f"{stats.get('caller_failed', 0)} fail")
    print(f"    Follow_env : {stats.get('follow_env_total', 0)} total, "
          f"{stats.get('follow_env_success', 0)} ok, "
          f"{stats.get('follow_env_failed', 0)} fail")
    print("=" * 70)
    print()


# ═══════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="Agent Caller Mode")
    ap.add_argument("slug", nargs="?", default=None)
    ap.add_argument("--source", "-s", default="otakudesu")
    ap.add_argument("--queue", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--clear-queue", action="store_true")
    args = ap.parse_args()

    cfg = get_config()
    log_dir = AGENT_DIR / cfg.log_dir
    setup_agent_logging(
        log_dir, "caller.log", cfg.log_level,
        cfg.log_max_bytes, cfg.log_backup_count,
    )

    if args.status:
        display_status()
        return

    if args.clear_queue:
        count = state.clear_caller_queue()
        logger.info(f"[Caller] Queue cleared: {count} slug")
        return

    if args.push:
        if not args.slug:
            logger.error("[Caller] --push butuh slug")
            sys.exit(1)
        pos = state.push_caller_slug(args.slug, source=args.source)
        if pos == -1:
            logger.info(f"[Caller] Slug '{args.slug}' sudah di queue")
        else:
            logger.info(f"[Caller] Slug '{args.slug}' ditambah (pos: {pos + 1})")
        return

    if args.queue:
        process_queue()
        return

    if args.slug:
        run_caller(args.slug, source=args.source)
        return

    ap.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n[Caller] Interrupted by user")
    except Exception as e:
        logger.exception(f"[Caller] Fatal error: {e}")