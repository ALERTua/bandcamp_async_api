"""Data models for Bandcamp API."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass
class SearchResultItem:
    """Base class for search result items."""

    type: str
    id: int
    name: str
    url: str


@dataclass
class SearchResultArtist(SearchResultItem):
    """Artist search result."""

    type: str = field(default="artist", init=False)
    location: str | None = None
    is_label: bool = False
    tags: list[str] | None = None
    image_url: str | None = None
    genre: str | None = None


@dataclass
class SearchResultAlbum(SearchResultItem):
    """Album search result."""

    type: str = field(default="album", init=False)
    artist_id: int = 0
    artist_name: str = ""
    artist_url: str = ""
    image_url: str | None = None
    tags: list[str] | None = None


@dataclass
class SearchResultTrack(SearchResultItem):
    """Track search result."""

    type: str = field(default="track", init=False)
    artist_id: int = 0
    artist_name: str = ""
    album_name: str = ""
    album_id: int | None = None
    artist_url: str = ""
    image_url: str | None = None


@dataclass
class BCArtist:
    """Bandcamp artist/band data.

    Based on /api/mobile/24/band_details response schema.
    Maps to API fields: band_id, name, subdomain, location_text,
    image_id, bio, tags, genre_name, etc.
    """

    id: int  # band_id from API
    name: str  # name from API
    url: str | None = None  # constructed from subdomain
    location: str | None = None  # location_text from API
    image_url: str | None = None  # constructed from image_id
    is_label: bool = False  # band.is_label from API
    bio: str | None = None  # bio from API
    tags: list[str] | None = None  # tags[].name from API
    genre: str | None = None  # genre_name from API


@dataclass
class BCAlbum:
    """Bandcamp album data.

    Based on /api/mobile/24/tralbum_details response schema.
    Maps to API fields: id, title/album_title, bandcamp_url, art_id,
    release_date, price, about, credits, tags, num_downloadable_tracks, etc.
    """

    id: int  # tralbum_id from API
    title: str  # title/album_title from API
    artist: BCArtist  # parsed from band data
    url: str | None = None  # bandcamp_url from API
    art_url: str | None = None  # constructed from art_id
    release_date: int | None = None  # release_date from API (Unix timestamp)
    price: dict[str, Any] | None = None  # {"currency": str, "amount": float}
    is_free: bool = False  # derived from price == 0
    is_preorder: bool = False  # is_preorder from API
    is_purchasable: bool = False  # is_purchasable from API
    is_set_price: bool = False  # is_set_price from API
    about: str | None = None  # about from API
    credits: str | None = None  # credits from API
    tags: list[str] | None = None  # tags[].name from API
    total_tracks: int = 0  # num_downloadable_tracks from API
    tracks: list["BCTrack"] | None = None  # parsed from tracks array
    type: str = "album"  # "album", "album-single", "track"

    # Advanced fields (from HTML scraping)
    copyright: str | None = None
    reviews: list[dict[str, Any]] | None = None
    supporters: list[dict[str, Any]] | None = None


@dataclass
class BCTrack:
    """Bandcamp track data.

    Based on /api/mobile/24/tralbum_details tracks array schema.
    Maps to API fields: track_id, title, duration, streaming_url,
    track_num, lyrics, about, credits, etc.
    """

    id: int  # track_id from API
    title: str  # title from API
    artist: BCArtist  # inherited from album or parsed separately
    album: BCAlbum | None = None  # parent album if part of album
    url: str | None = None  # constructed or from API
    duration: float | None = None  # duration from API (seconds)
    streaming_url: dict[str, str] | None = None  # streaming_url from API
    track_number: int = 0  # track_num from API
    lyrics: str | None = None  # lyrics from API
    about: str | None = None  # about from API
    credits: str | None = None  # credits from API
    type: str = "track"


@dataclass
class CollectionItem:
    """Item from user's collection.

    Based on /api/fancollection/1/* responses schema.
    Maps to API fields: item_type, item_id, band_id, tralbum_type,
    band_name, item_title, item_url, art_id, etc.
    """

    item_type: str  # item_type from API ("album", "track", "band")
    item_id: int  # item_id from API
    band_id: int  # band_id from API
    tralbum_type: str | None = (
        None  # tralbum_type from API ("a" for album, "t" for track)
    )
    band_name: str = ""  # band_name from API
    item_title: str = ""  # item_title from API
    item_url: str = ""  # item_url from API
    art_id: int | None = None  # art_id from API
    num_streamable_tracks: int | None = None  # num_streamable_tracks from API
    is_purchasable: bool = False  # is_purchasable from API
    price: float | None = None  # price from API


@dataclass
class CollectionSummary:
    """User's collection summary.

    Based on /api/fan/2/collection_summary and /api/fancollection/1/* responses.
    Contains fan_id from summary and paginated items from collection endpoints.
    """

    fan_id: int  # fan_id from collection_summary
    items: list[CollectionItem]  # items from collection endpoints
    has_more: bool = False  # has_more from API responses
    last_token: str | None = None  # last_token from API responses


class CollectionType(Enum):
    """Collection types for Bandcamp API endpoints."""

    COLLECTION = "collection_items"
    WISHLIST = "wishlist_items"
    FOLLOWING = "following_bands"
