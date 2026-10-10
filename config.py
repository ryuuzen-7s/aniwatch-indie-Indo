"""
config.py — Konfigurasi global (single mirror per source).
"""
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from pydantic import Field, field_validator, PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import dotenv_values


ROOT = Path(__file__).parent.resolve()
ENV_FILE = ROOT / ".env"


# ═══════════════════════════════════════════════════════════
#  SOURCE CONFIG
# ═══════════════════════════════════════════════════════════
@dataclass
class SourceConfig:
    """Konfigurasi satu source."""
    name: str
    enabled: bool = True
    base_url: str = ""
    shortener_hosts: List[str] = field(default_factory=list)

    @property
    def mirrors(self) -> List[str]:
        """Kompatibilitas: return list single mirror."""
        return [self.base_url] if self.base_url else []

    def __repr__(self):
        icon = "✅" if self.enabled else "❌"
        return f"<Source {icon} {self.name}: {self.base_url}>"


# ═══════════════════════════════════════════════════════════
#  PARSER .env
# ═══════════════════════════════════════════════════════════
RESERVED_PREFIXES = {
    "APP", "SERVER", "DB", "DATABASE", "CACHE",
    "RESOLVER", "ZROK", "HTTP", "LOG", "DEBUG",
    "DEFAULT",
}


def load_source_from_env(raw: dict, prefix: str) -> Optional[SourceConfig]:
    """Baca source berdasarkan prefix."""
    prefix_up = prefix.upper()
    enabled_key = f"{prefix_up}_ENABLED"

    if enabled_key not in raw:
        return None

    enabled = raw.get(enabled_key, "true").lower() in ("true", "1", "yes", "on")
    base_url = (raw.get(f"{prefix_up}_BASE_URL", "") or "").strip().rstrip("/")

    # Fallback: coba MIRROR_1 (kompatibilitas dengan .env lama)
    if not base_url:
        base_url = (raw.get(f"{prefix_up}_MIRROR_1", "") or "").strip().rstrip("/")

    if not base_url.startswith("http"):
        return None

    shortener_str = raw.get(f"{prefix_up}_SHORTENER_HOSTS", "") or ""
    shortener_hosts = [h.strip() for h in shortener_str.split(",") if h.strip()]

    return SourceConfig(
        name=prefix.lower(),
        enabled=enabled,
        base_url=base_url,
        shortener_hosts=shortener_hosts,
    )


def load_all_sources(env_file: Path) -> Dict[str, SourceConfig]:
    sources: Dict[str, SourceConfig] = {}
    if not env_file.exists():
        return sources

    raw = dotenv_values(env_file)

    prefixes = set()
    for key in raw.keys():
        if not key:
            continue
        key_up = key.upper()
        if key_up.endswith("_ENABLED"):
            prefix = key_up.rsplit("_", 1)[0]
            if prefix in RESERVED_PREFIXES:
                continue
            prefixes.add(prefix)

    for prefix in sorted(prefixes):
        src = load_source_from_env(raw, prefix)
        if src:
            sources[src.name] = src

    return sources


# ═══════════════════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════════════════
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # APP
    app_name: str = "AniWatch API"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # SERVER
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    #  API METHOD RESTRICTION
    allowed_methods: str = "GET,POST"
    method_excluded_paths: str = "/keys,/docs,/redoc,/openapi.json,/monitor"

    # SOURCE
    default_source: str = "otakudesu"

    # HTTP
    request_timeout: int = 15
    max_retry: int = 3
    retry_backoff: float = 1.5
    rate_limit_delay: float = 1.0
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # DATABASE
    db_path: str = "data/db/aniwatch.db"
    db_echo: bool = False

    # CACHE
    cache_enabled: bool = True
    cache_memory_size: int = 1000
    cache_ttl_anime: int = 604800
    cache_ttl_episode_list: int = 86400
    cache_ttl_episode_detail: int = 3600
    cache_ttl_download: int = 1800
    cache_ttl_poster: int = 2592000
    cache_ttl_search: int = 3600
    cache_ttl_now: int = 300
    cache_ttl_season: int = 86400

    # RESOLVER
    resolver_enabled: bool = True
    resolver_timeout: int = 10
    resolver_max_workers: int = 5

    # ZROK
    zrok_enabled: bool = False
    zrok_reserved_token: str = ""

    # PRIVATE
    _sources_cache: Optional[Dict[str, SourceConfig]] = PrivateAttr(default=None)

    # ═══════════════════════════════════════════════════════
    #  PROPERTIES
    # ═══════════════════════════════════════════════════════
    @property
    def sources(self) -> Dict[str, SourceConfig]:
        if self._sources_cache is None:
            object.__setattr__(self, "_sources_cache", load_all_sources(ENV_FILE))
        return self._sources_cache

    def reload_sources(self) -> Dict[str, SourceConfig]:
        object.__setattr__(self, "_sources_cache", load_all_sources(ENV_FILE))
        return self._sources_cache

    @property
    def active_sources(self) -> Dict[str, SourceConfig]:
        return {k: v for k, v in self.sources.items() if v.enabled}

    def get_source(self, name: str) -> Optional[SourceConfig]:
        return self.sources.get(name.lower())

    @property
    def base_url(self) -> str:
        src = self.get_source(self.default_source)
        if src and src.base_url:
            return src.base_url
        for s in self.active_sources.values():
            if s.base_url:
                return s.base_url
        return ""

    @property
    def headers(self) -> dict:
        return {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": f"{self.base_url}/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def headers_for(self, source_name: str) -> dict:
        src = self.get_source(source_name)
        ref = (src.base_url if src and src.base_url else self.base_url)
        h = self.headers.copy()
        if ref:
            h["Referer"] = f"{ref}/"
        return h

    @property
    def db_full_path(self) -> Path:
        p = Path(self.db_path)
        if not p.is_absolute():
            p = ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
        
    @property
    def allowed_methods_set(self) -> set[str]:
        """Set method yang diizinkan (parsed dari string)."""
        return {
            m.strip().upper()
            for m in self.allowed_methods.split(",")
            if m.strip()
        }

    @property
    def method_excluded_paths_tuple(self) -> tuple[str, ...]:
        """Tuple path yang di-exclude (parsed dari string)."""
        return tuple(
            p.strip()
            for p in self.method_excluded_paths.split(",")
            if p.strip()
        )
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_up = v.upper()
        if v_up not in allowed:
            raise ValueError(f"LOG_LEVEL harus salah satu dari {allowed}")
        return v_up


# Singleton
settings = Settings()


# ═══════════════════════════════════════════════════════════
#  TEST
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 62)
    print("  ANIWATCH CONFIG (SINGLE MIRROR)")
    print("=" * 62)
    print(f"  App          : {settings.app_name} v{settings.app_version}")
    print(f"  Debug        : {settings.debug}")
    print(f"  Default src  : {settings.default_source}")
    print()

    if not settings.sources:
        print("  ⚠️  Tidak ada source terdeteksi!")
    else:
        for name, src in settings.sources.items():
            icon = "✅" if src.enabled else "❌"
            print(f"  {icon} [{name.upper()}]")
            print(f"      Base URL : {src.base_url}")
            if src.shortener_hosts:
                print(f"      Shortener: {', '.join(src.shortener_hosts)}")

    print()
    print(f"  DB           : {settings.db_full_path}")
    print("=" * 62)