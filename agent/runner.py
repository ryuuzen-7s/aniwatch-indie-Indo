"""
agent/runner.py - Runner: scrape semua slug dari config + ongoing.

Jalankan:
    python agent/runner.py              # scrape semua slug
    python agent/runner.py --dry-run    # cek dulu
    python agent/runner.py --slug xxx   # scrape 1 slug
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
from core.fetcher import fetch


# ═══════════════════════════════════════════════════════════
#  LOGGING SETUP
# ═══════════════════════════════════════════════════════════
def setup_logging(log_dir: Path, log_file: str, level: str,
                  max_bytes: int, backup_count: int):
    """Setup logging dengan rotasi file."""
    from logging.handlers import RotatingFileHandler

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level, logging.INFO))

    # Hapus handler lama
    logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                      datefmt="%H:%M:%S"))
    logger.addHandler(ch)

    # File handler (rotasi)
    fh = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(fh)

    return log_path


# ═══════════════════════════════════════════════════════════
#  FETCH ONGOING SLUGS
# ═══════════════════════════════════════════════════════════
def fetch_ongoing_slugs(limit: int = 20) -> list:
    """Ambil slug anime on-going dari Otakudesu."""
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
    return slugs


# ═══════════════════════════════════════════════════════════
#  MAIN RUNNER
# ═══════════════════════════════════════════════════════════
def run(
    dry_run: bool = False,
    single_slug: str = None,
    skip_ongoing: bool = False,
):
    """Jalankan agent."""
    cfg = get_config()

    # Setup logging
    log_dir = AGENT_DIR / cfg.log_dir
    log_path = setup_logging(
        log_dir, cfg.log_file, cfg.log_level,
        cfg.log_max_bytes, cfg.log_backup_count,
    )

    logger = logging.getLogger("agent.runner")

    logger.info("=" * 70)
    logger.info(f"  ANIWATCH AGENT RUN — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    logger.info(f"  Log file: {log_path}")

    # Kumpulkan slugs
    slugs = []
    sources = {}  # slug -> "config" | "ongoing"

    if single_slug:
        slugs = [single_slug]
        sources[single_slug] = "cli"
    else:
        # 1. Dari config
        for s in cfg.slugs:
            if s not in slugs:
                slugs.append(s)
                sources[s] = "config"

        # 2. Dari ongoing
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

    # Scrape
    t_start = time.time()
    stats = {"ok": 0, "skip": 0, "fail": 0}
    fails = []

    for i, slug in enumerate(slugs, 1):
        logger.info(f"[{i}/{total}] Scrape: {slug} ({sources[slug]})")

        res = scrape_one(
            slug,
            follow_all=cfg.follow_all_episodes,
            skip_existing=cfg.skip_existing,
        )

        if res["status"] == "ok":
            c = res["counters"]
            logger.info(
                f"    OK ({res['duration']:.1f}s) — "
                f"{c['anime']} anime, {c['episodes']} ep, {c['downloads']} dl"
            )
            stats["ok"] += 1
        elif res["status"] == "skip":
            logger.info(f"    SKIP — {res['error']}")
            stats["skip"] += 1
        else:
            logger.warning(f"    FAIL ({res['duration']:.1f}s) — {res['error']}")
            stats["fail"] += 1
            fails.append({"slug": slug, "error": res["error"]})

        # Jeda
        if i < total:
            time.sleep(cfg.delay_between)

    # Ringkasan
    dt = time.time() - t_start
    logger.info("=" * 70)
    logger.info(f"  SELESAI — {dt:.1f}s")
    logger.info(f"  OK   : {stats['ok']}")
    logger.info(f"  SKIP : {stats['skip']}")
    logger.info(f"  FAIL : {stats['fail']}")
    if fails:
        logger.info("  Gagal:")
        for f in fails:
            logger.info(f"    - {f['slug']}: {f['error'][:80]}")
    logger.info("=" * 70)

    return stats


# ═══════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="AniWatch Agent Runner")
    ap.add_argument("--dry-run", action="store_true",
                    help="Cek daftar slug tanpa scrape")
    ap.add_argument("--slug", type=str, default=None,
                    help="Scrape 1 slug saja")
    ap.add_argument("--skip-ongoing", action="store_true",
                    help="Skip auto-ongoing")
    args = ap.parse_args()

    try:
        run(
            dry_run=args.dry_run,
            single_slug=args.slug,
            skip_ongoing=args.skip_ongoing,
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        logging.exception(f"Fatal error: {e}")


if __name__ == "__main__":
    main()