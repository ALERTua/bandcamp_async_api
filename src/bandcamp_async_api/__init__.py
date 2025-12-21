"""Bandcamp API - standalone async client for Bandcamp."""

from .client import BandcampAPIClient, BandcampAPIError, BandcampNotFoundError
from .models import (
    BCAlbum,
    BCArtist,
    BCTrack,
    CollectionItem,
    CollectionSummary,
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
    "BandcampNotFoundError",
    "CollectionItem",
    "CollectionSummary",
    "SearchResultAlbum",
    "SearchResultArtist",
    "SearchResultItem",
    "SearchResultTrack",
]
