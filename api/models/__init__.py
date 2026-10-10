"""
api.models — Pydantic schemas.
"""
from .common import (
    APIResponse, ErrorDetail, MetaInfo, PaginationMeta,
    success_response, error_response, paginated_response,
)
from .anime import (
    AnimeMetadata, AnimeItem, AnimeDetail, EpisodeBrief,
    build_anime_item, build_anime_detail,
)
from .episode import (
    StreamItem, DownloadItem, DownloadsSummary,
    EpisodeItem, EpisodeDetail, EpisodeListResponse,
    build_episode_item, build_download_item,
    build_downloads_summary, build_episode_detail,
    build_episode_list_response,
)
from .search import (
    SearchResultItem, SearchResponse, build_search_item,
)
from .poster import PosterResponse
from .season import SeasonResponse, SeasonAnimeItem
from .now import NowResponse, NowAnimeItem
from .report import ReportRequest, ReportResponse
from .link import LinkAskRequest, LinkAskResponse
from .empty import EmptyRequest, EmptyResponse

__all__ = [
    "APIResponse", "ErrorDetail", "MetaInfo", "PaginationMeta",
    "success_response", "error_response", "paginated_response",
    "AnimeMetadata", "AnimeItem", "AnimeDetail", "EpisodeBrief",
    "build_anime_item", "build_anime_detail",
    "StreamItem", "DownloadItem", "DownloadsSummary",
    "EpisodeItem", "EpisodeDetail", "EpisodeListResponse",
    "build_episode_item", "build_download_item",
    "build_downloads_summary", "build_episode_detail",
    "build_episode_list_response",
    "SearchResultItem", "SearchResponse", "build_search_item",
    "PosterResponse",
    "SeasonResponse", "SeasonAnimeItem",
    "NowResponse", "NowAnimeItem",
    "ReportRequest", "ReportResponse",
    "LinkAskRequest", "LinkAskResponse",
    "EmptyRequest", "EmptyResponse",
]
