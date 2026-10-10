"""
db/models.py — ORM models untuk AniWatch.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Integer, String, Text, Boolean, Float,
    DateTime, ForeignKey, JSON, Index, UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship,
)


# ═══════════════════════════════════════════════════════════
#  BASE
# ═══════════════════════════════════════════════════════════
def utc_now() -> datetime:
    """Timezone-aware UTC now."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class ORM."""
    pass


# ═══════════════════════════════════════════════════════════
#  ANIME
# ═══════════════════════════════════════════════════════════
class Anime(Base):
    __tablename__ = "anime"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Identitas
    source: Mapped[str] = mapped_column(String(50), default="otakudesu", index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), default="")

    # Metadata
    title: Mapped[str] = mapped_column(String(500), default="")
    title_jp: Mapped[str] = mapped_column(String(500), default="")
    synopsis: Mapped[str] = mapped_column(Text, default="")
    poster_url: Mapped[str] = mapped_column(String(500), default="")

    # Detail
    studio: Mapped[str] = mapped_column(String(200), default="")
    producer: Mapped[str] = mapped_column(String(200), default="")
    type: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(50), default="")
    duration: Mapped[str] = mapped_column(String(100), default="")
    release_date: Mapped[str] = mapped_column(String(100), default="")
    total_episode: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # JSON
    genres: Mapped[list] = mapped_column(JSON, default=list)
    info: Mapped[dict] = mapped_column(JSON, default=dict)

    # Timestamps
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationship
    episodes: Mapped[List["Episode"]] = relationship(
        "Episode",
        back_populates="anime",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Index komposit
    __table_args__ = (
        Index("ix_anime_source_slug", "source", "slug"),
    )

    def to_dict(self, include_episodes: bool = False) -> dict:
        """Serialize ke dict (untuk API response)."""
        data = {
            "id": self.id,
            "source": self.source,
            "slug": self.slug,
            "url": self.url,
            "title": self.title,
            "title_jp": self.title_jp,
            "synopsis": self.synopsis,
            "poster_url": self.poster_url,
            "studio": self.studio,
            "producer": self.producer,
            "type": self.type,
            "status": self.status,
            "duration": self.duration,
            "release_date": self.release_date,
            "total_episode": self.total_episode,
            "rating": self.rating,
            "genres": self.genres or [],
            "info": self.info or {},
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_episodes:
            data["episodes"] = [e.to_dict() for e in self.episodes]
        return data

    def __repr__(self):
        return f"<Anime {self.slug} | {self.title[:30]}>"


# ═══════════════════════════════════════════════════════════
#  EPISODE
# ═══════════════════════════════════════════════════════════
class Episode(Base):
    __tablename__ = "episode"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anime_id: Mapped[int] = mapped_column(
        ForeignKey("anime.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Identitas
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), default="")
    title: Mapped[str] = mapped_column(String(500), default="")
    episode_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    # Stream (1 episode bisa multiple stream, tapi biasanya 1)
    stream_url: Mapped[str] = mapped_column(String(500), default="")
    stream_host: Mapped[str] = mapped_column(String(100), default="")

    # Timestamps
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationship
    anime: Mapped["Anime"] = relationship("Anime", back_populates="episodes")
    downloads: Mapped[List["DownloadLink"]] = relationship(
        "DownloadLink",
        back_populates="episode",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_episode_anime_number", "anime_id", "episode_number"),
    )

    def to_dict(self, include_downloads: bool = False) -> dict:
        data = {
            "id": self.id,
            "anime_id": self.anime_id,
            "slug": self.slug,
            "url": self.url,
            "title": self.title,
            "episode_number": self.episode_number,
            "stream_url": self.stream_url,
            "stream_host": self.stream_host,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
        }
        if include_downloads:
            data["downloads"] = [d.to_dict() for d in self.downloads]
        return data

    def __repr__(self):
        return f"<Episode {self.slug} | ep#{self.episode_number}>"


# ═══════════════════════════════════════════════════════════
#  DOWNLOAD LINK
# ═══════════════════════════════════════════════════════════
class DownloadLink(Base):
    __tablename__ = "download_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    episode_id: Mapped[int] = mapped_column(
        ForeignKey("episode.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Data link
    quality: Mapped[str] = mapped_column(String(50), default="", index=True)
    host: Mapped[str] = mapped_column(String(100), default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    final_url: Mapped[str] = mapped_column(String(500), default="")
    final_host: Mapped[str] = mapped_column(String(100), default="")

    # Status
    status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_alive: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    error: Mapped[str] = mapped_column(String(255), default="")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    episode: Mapped["Episode"] = relationship("Episode", back_populates="downloads")

    __table_args__ = (
        UniqueConstraint("episode_id", "quality", "host", name="uq_ep_quality_host"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "episode_id": self.episode_id,
            "quality": self.quality,
            "host": self.host,
            "url": self.url,
            "final_url": self.final_url,
            "final_host": self.final_host,
            "status": self.status,
            "is_alive": self.is_alive,
            "error": self.error,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
        }

    def __repr__(self):
        icon = "✅" if self.is_alive else "❌"
        return f"<DL {icon} {self.quality}/{self.host}>"


# ═══════════════════════════════════════════════════════════
#  REPORT
# ═══════════════════════════════════════════════════════════
class Report(Base):
    __tablename__ = "report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="", index=True)
    url: Mapped[str] = mapped_column(String(500), default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    reporter_ip: Mapped[str] = mapped_column(String(45), default="")
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "type": self.type,
            "url": self.url,
            "reason": self.reason,
            "resolved": self.resolved,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Report {self.type} | {self.slug}>"


# ═══════════════════════════════════════════════════════════
#  USER
# ═══════════════════════════════════════════════════════════
class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self, include_secret: bool = False) -> dict:
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        return data

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# ═══════════════════════════════════════════════════════════
#  API KEY
# ═══════════════════════════════════════════════════════════
class ApiKey(Base):
    __tablename__ = "api_key"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), index=True, default="")
    name: Mapped[str] = mapped_column(String(100), default="")
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=True, index=True
    )
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    rate_limit: Mapped[int] = mapped_column(Integer, default=100)
    max_requests: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key_prefix": self.key_prefix,
            "name": self.name,
            "user_id": self.user_id,
            "role": self.role,
            "is_active": self.is_active,
            "rate_limit": self.rate_limit,
            "request_count": self.request_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }

    def __repr__(self):
        return f"<ApiKey {self.key_prefix}... ({self.role})>"