"""
agent/config.py - Loader config dari agent/.env.
"""
import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from dotenv import dotenv_values


AGENT_DIR = Path(__file__).parent.resolve()
ENV_FILE = AGENT_DIR / ".env"


@dataclass
class AgentConfig:
    """Config agent."""
    # Source
    otakudesu_url: str = "https://otakudesu.blog"

    # Slugs
    slugs: List[str] = None

    # Auto ongoing
    scrape_ongoing: bool = True
    ongoing_limit: int = 20

    # Behavior
    follow_all_episodes: bool = False
    skip_existing: bool = True
    delay_between: float = 2.0
    max_retry: int = 2

    # Schedule
    interval_hours: int = 6
    cron_time: str = "03:00"
    timezone: str = "Asia/Jakarta"

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "agent.log"
    log_max_bytes: int = 5_242_880
    log_backup_count: int = 5

    # DB
    db_path: str = "../data/db/aniwatch.db"


def load_config() -> AgentConfig:
    """Load config dari .env."""
    if not ENV_FILE.exists():
        print(f"WARNING: {ENV_FILE} tidak ada, pakai default")
        raw = {}
    else:
        raw = dotenv_values(ENV_FILE)

    # Kumpulkan slugs (SLUG_1, SLUG_2, ...)
    slugs = {}
    for key, value in raw.items():
        if not key or not value:
            continue
        key_up = key.upper()
        if key_up.startswith("SLUG_"):
            try:
                num = int(key_up.split("_", 1)[1])
                slugs[num] = value.strip()
            except (ValueError, IndexError):
                continue

    slug_list = [slugs[k] for k in sorted(slugs.keys())]

    # Helper parse
    def get_bool(key: str, default: bool) -> bool:
        v = raw.get(key, str(default)).lower()
        return v in ("true", "1", "yes", "on")

    def get_int(key: str, default: int) -> int:
        try:
            return int(raw.get(key, default))
        except (ValueError, TypeError):
            return default

    def get_float(key: str, default: float) -> float:
        try:
            return float(raw.get(key, default))
        except (ValueError, TypeError):
            return default

    return AgentConfig(
        otakudesu_url=raw.get("OTAKUDESU_URL", "https://otakudesu.blog").rstrip("/"),
        slugs=slug_list,
        scrape_ongoing=get_bool("SCRAPE_ONGOING", True),
        ongoing_limit=get_int("ONGOING_LIMIT", 20),
        follow_all_episodes=get_bool("FOLLOW_ALL_EPISODES", False),
        skip_existing=get_bool("SKIP_EXISTING", True),
        delay_between=get_float("DELAY_BETWEEN", 2.0),
        max_retry=get_int("MAX_RETRY", 2),
        interval_hours=get_int("INTERVAL_HOURS", 6),
        cron_time=raw.get("CRON_TIME", "03:00"),
        timezone=raw.get("TIMEZONE", "Asia/Jakarta"),
        log_level=raw.get("LOG_LEVEL", "INFO").upper(),
        log_dir=raw.get("LOG_DIR", "logs"),
        log_file=raw.get("LOG_FILE", "agent.log"),
        log_max_bytes=get_int("LOG_MAX_BYTES", 5_242_880),
        log_backup_count=get_int("LOG_BACKUP_COUNT", 5),
        db_path=raw.get("DB_PATH", "../data/db/aniwatch.db"),
    )


# Singleton (lazy load)
_config: Optional[AgentConfig] = None


def get_config() -> AgentConfig:
    """Ambil config (cached)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> AgentConfig:
    """Force reload."""
    global _config
    _config = load_config()
    return _config


if __name__ == "__main__":
    cfg = load_config()
    print("=" * 60)
    print("  AGENT CONFIG")
    print("=" * 60)
    print(f"  Otakudesu URL : {cfg.otakudesu_url}")
    print(f"  Slugs         : {len(cfg.slugs)}")
    for i, s in enumerate(cfg.slugs, 1):
        print(f"    [{i}] {s}")
    print(f"  Scrape ongoing: {cfg.scrape_ongoing}")
    print(f"  Ongoing limit : {cfg.ongoing_limit}")
    print(f"  Follow all ep : {cfg.follow_all_episodes}")
    print(f"  Skip existing : {cfg.skip_existing}")
    print(f"  Interval      : {cfg.interval_hours} jam")
    print(f"  Cron time     : {cfg.cron_time}")
    print(f"  Timezone      : {cfg.timezone}")
    print("=" * 60)