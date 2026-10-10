"""
api/models/link.py — Schema untuk linkask.
"""
from typing import Optional

from pydantic import BaseModel, Field


class LinkAskRequest(BaseModel):
    """Body untuk POST /share/linkask/{slug}."""
    type: str = Field("all", pattern="^(stream|download|all)$", description="stream|download|all")
    deep: bool = Field(False, description="Resolve shortener (lambat tapi akurat)")


class LinkAskResponse(BaseModel):
    """Response linkask."""
    slug: str
    has_link: bool = False
    stream_count: int = 0
    download_count: int = 0
    alive_count: int = 0
    dead_count: int = 0
    checked_deep: bool = False