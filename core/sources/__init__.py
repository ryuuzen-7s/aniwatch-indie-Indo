"""
core/sources/__init__.py — Registry parser per source.
"""
from typing import Dict, Type, Optional

from .base import BaseParser
from .otakudesu import OtakudesuParser


# ═══════════════════════════════════════════════════════════
#  REGISTRY
# ═══════════════════════════════════════════════════════════
_PARSERS: Dict[str, Type[BaseParser]] = {
    "otakudesu": OtakudesuParser,
    # "kuramanime": KuramanimeParser,  # nanti
    # "animeindo": AnimeindoParser,    # nanti
}


def get_parser(source: str) -> Optional[Type[BaseParser]]:
    """Ambil class parser berdasarkan nama source."""
    return _PARSERS.get(source.lower())


def list_parsers() -> Dict[str, Type[BaseParser]]:
    """List semua parser yang terdaftar."""
    return _PARSERS.copy()


__all__ = [
    "BaseParser",
    "OtakudesuParser",
    "get_parser",
    "list_parsers",
]