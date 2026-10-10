"""
api/models/poster.py — Schema untuk poster anime.
"""
from typing import Optional

from pydantic import BaseModel


class PosterResponse(BaseModel):
    """Response untuk /share/posterid/{slug}."""
    slug: str
    title: Optional[str] = None
    poster_url: Optional[str] = None