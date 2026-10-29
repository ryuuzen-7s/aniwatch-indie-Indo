"""
agent/runner.py — Opsi 2: Follow .env mode.
"""
import sys
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dotenv import dotenv_values, set_key

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
from core.fetcher import fetch


# ═══════════════════════════════════════════════════════════
#  AUTO SAVE SLUG (MAX 20, ANTI DUPLIKAT, FIFO)
# ═══════════════════════════════════════════════════════════
def save_slugs_to_env(new_slugs: list):
    """Simpan slug baru ke agent/.env (Maksimal 20, skip duplikat)."""
    env_file = AGENT_DIR / ".env"
    if not env_file.exists():
        return

    raw = dotenv_values(env_file)
    
    # 1. Kumpulkan slug yang sudah ada
    existing = []
    for key, val in raw.items():
        if key and key.startswith("SLUG_") and val:
            existing.append(val.strip())

    # 2. Filter: Hanya ambil yang belum ada di .env
    to_add = []
    for slug in new_slugs:
        if slug not in existing and slug not in to_add:
            to_add.append(slug)

    if not to_add:
        return  # Tidak ada slug baru

    # 3. Gabungkan dan batasi maksimal 20 (FIFO: buang yang paling lama)
    combined = existing + to_add
    if len(combined) > 20:
        combined = combined[-20:]  # Ambil 20 terakhir

    # 4. Tulis ulang SLUG_1 sampai SLUG_20 ke .env
    for i, slug in enumerate(combined, 1):
        set_key(env_file, f"SLUG_{i}", slug)

    logging.getLogger("agent.runner").info(
        f"Auto-save: {len(to_add)} slug baru. Total sekarang: {len(combined)}/20"
    )


# ═══════════════════════════════════════════════════════════
#  FETCH ONGOING SLUGS
# ═══════════════════════════════════════════════════════════
def fetch_ongoing_slugs(limit: int = 20) -> list:
    logger = logging.getLogger(__name__)
    logger.info("Fetch daftar on-going dari Otakudesu...")

    try:
        soup, _ = fetch("/ongoing-anime/", source="otakudesu")
    except Exception as e:
        logger.error(f"Fetch ongoing gagal: {e}")
        return []

    if not soup:
        return []

    slugs = []
    seen = set()

    for li in soup.select(".venz > ul > li"):
        link = li.select_one(".jdlflx a") or li.select_one("a")
        if not link:
            continue
        href = link.get("href", "")
        if "/anime/" not in href:
            continue
        slug = href.rstrip("/").split("/")[-1]
        if slug and slug not in seen:
            seen.add(slug)
            slugs.append(slug)

    if limit > 0:
        slugs = slugs[:limit]

    logger.info(f"Ditemukan {len(slugs)} anime on-going")
    save_slugs_to_env(slugs)

    return slugs


# ═══════════════════════════════════════════════════════════
#  MAIN RUNNER
# ═══════════════════════════════════════════════════════════
def run(
    dry_run: bool = False,
    single_slug: str = None,
    skip_ongoing: bool = False,
):
    cfg = get_config()

    log_dir = AGENT_DIR / cfg.log_dir
    log_path = setup_agent_logging(
        log_dir, "agent.log", cfg.log_level,
        cfg.log_max_bytes, cfg.log_backup_count,
    )

    logger = logging.getLogger("agent.runner")

    logger.info("=" * 70)
    logger.info(f"  AGENT FOLLOW_ENV — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    logger.info(f"  Log file: {log_path}")

    slugs = []
    sources = {}

    if single_slug:
        slugs = [single_slug]
        sources[single_slug] = "cli"
    else:
        for s in cfg.slugs:
            if s not in slugs:
                slugs.append(s)
                sources[s] = "config"

        if cfg.scrape_ongoing and not skip_ongoing:
            ongoing = fetch_ongoing_slugs(cfg.ongoing_limit)
            for s in ongoing:
                if s not in slugs:
                    slugs.append(s)
                    sources[s] = "ongoing"

    total = len(slugs)
    logger.info(f"  Total slug: {total}")
    logger.info(f"  Skip existing: {cfg.skip_existing}")
    logger.info(f"  Follow all episodes: {cfg.follow_all_episodes}")
    logger.info(f"  Delay: {cfg.delay_between}s")
    logger.info("=" * 70)

    if dry_run:
        logger.info("DRY RUN - tidak scrape:")
        for i, s in enumerate(slugs, 1):
            logger.info(f"  [{i}/{total}] {s} ({sources[s]})")
        return

    t_start = time.time()
    stats = {"ok": 0, "skip": 0, "fail": 0}
    fails = []

    for i, slug in enumerate(slugs, 1):
        if cfg.caller_priority and state.is_caller_running():
            logger.info(f"[Runner] Caller prioritas, pause follow_env...")
            state.pause_follow_env()
            while state.is_caller_running():
                time.sleep(1)
            logger.info(f"[Runner] Caller selesai, resume follow_env...")
            state.resume_follow_env()

        logger.info(f"[{i}/{total}] Scrape: {slug} ({sources[slug]})")

        # Menggunakan follow_all=True memastikan semua episode diambil, bukan cuma eps 1
        res = scrape_one(
            slug,
            follow_all=True, 
            skip_existing=cfg.skip_existing,
        )

        if res["status"] == "ok":
            c = res["counters"]
            logger.info(f"    OK ({res['duration']:.1f}s) — {c['anime']} anime, {c['episodes']} ep, {c['downloads']} dl")
            stats["ok"] += 1
        elif res["status"] == "skip":
            logger.info(f"    SKIP — {res['error']}")
            stats["skip"] += 1
        else:
            logger.warning(f"    FAIL ({res['duration']:.1f}s) — {res['error']}")
            stats["fail"] += 1
            fails.append({"slug": slug, "error": res["error"]})

        if i < total:
            time.sleep(cfg.delay_between)

    dt = time.time() - t_start
    logger.info("=" * 70)
    logger.info(f"  SELESAI — {dt:.1f}s")
    logger.info(f"  OK   : {stats['ok']}")
    logger.info(f"  SKIP : {stats['skip']}")
    logger.info(f"  FAIL : {stats['fail']}")
    logger.info("=" * 70)

    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--slug", type=str, default=None)
    ap.add_argument("--skip-ongoing", action="store_true")
    args = ap.parse_args()

    try:
        run(dry_run=args.dry_run, single_slug=args.slug, skip_ongoing=args.skip_ongoing)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        logging.exception(f"Fatal error: {e}")


if __name__ == "__main__":
    main()