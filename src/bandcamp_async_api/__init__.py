"""Bandcamp API - standalone async client for Bandcamp."""

from .client import (
    BandcampAPIClient,
    BandcampAPIError,
    BandcampNotFoundError,
    BandcampMustBeLoggedInError,
    BandcampRateLimitError,
)
from .models import (
    BCAlbum,
    BCArtist,
    BCTrack,
    CollectionItem,
    CollectionSummary,
    FanItem,
    FollowingItem,
    SearchResultAlbum,
    SearchResultArtist,
    SearchResultItem,
    SearchResultTrack,
)

__all__ = [
    "BCAlbum",
    "BCArtist",
    "BCTrack",
    "BandcampAPIClient",
    "BandcampAPIError",
    "BandcampMustBeLoggedInError",
    "BandcampNotFoundError",
    "BandcampRateLimitError",
    "CollectionItem",
    "CollectionSummary",
    "FanItem",
    "FollowingItem",
    "SearchResultAlbum",
    "SearchResultArtist",
    "SearchResultItem",
    "SearchResultTrack",
]
