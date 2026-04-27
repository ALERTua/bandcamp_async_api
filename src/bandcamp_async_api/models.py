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

    # The explicit per-album performer credit (`tralbum_artist` from the
    # API). None when the API didn't set one, in which case the album is
    # by the band itself (use `artist.name`). When set and different from
    # `artist.name` the album is published on the band's page but
    # performed by someone else — typical for label releases (e.g. an
    # album on `audiophob.bandcamp.com` whose performer is "Mortaja").
    tralbum_artist: str | None = None

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

    # Mirror of BCAlbum.tralbum_artist for tracks fetched directly
    # (standalone tracks where `album` is None). For tracks parsed from
    # inside an album this stays None — the album already carries the
    # performer credit.
    tralbum_artist: str | None = None


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
    token: str | None = None  # token from API (used for pagination)


@dataclass
class FollowingItem:
    """A band/artist from the user's following list.

    Based on /api/fancollection/1/following_bands response schema.
    The response uses different field names than collection/wishlist endpoints.
    Items are returned in a "followeers" array (Bandcamp's typo) with fields:
    band_id, name, url_hints, image_id, location, date_followed, token, etc.
    """

    band_id: int  # band_id from API
    name: str = ""  # name from API
    url: str | None = None  # constructed from url_hints.subdomain
    image_url: str | None = None  # constructed from image_id
    location: str | None = None  # location from API
    date_followed: str | None = None  # date_followed from API
    is_label: bool = False  # is_label from API
    token: str | None = None  # token from API (used for pagination)


@dataclass
class FanItem:
    """A fan/user from following_fans or followers endpoints.

    Based on /api/fancollection/1/following_fans and /api/fancollection/1/followers
    response schemas. Used for both "fans I follow" and "fans who follow me".
    """

    fan_id: int  # fan_id from API
    name: str = ""  # name from API
    url: str | None = None  # trackpipe_url from API
    image_url: str | None = None  # constructed from image_id
    location: str | None = None  # location from API
    date_followed: str | None = None  # date_followed from API
    is_following: bool = False  # is_following from API
    token: str | None = None  # token from API (used for pagination)


@dataclass
class CollectionSummary:
    """User's collection summary.

    Based on /api/fan/2/collection_summary and /api/fancollection/1/* responses.
    Contains fan_id from summary and paginated items from collection endpoints.
    """

    fan_id: int  # fan_id from collection_summary
    items: list[
        CollectionItem | FollowingItem | FanItem
    ]  # items from collection endpoints
    has_more: bool = False  # has_more from API responses
    last_token: str | None = None  # last_token from API responses


class CollectionType(Enum):
    """Collection types for Bandcamp API endpoints."""

    COLLECTION = "collection_items"
    WISHLIST = "wishlist_items"
    FOLLOWING = "following_bands"
    FOLLOWING_FANS = "following_fans"
    FOLLOWERS = "followers"


@dataclass
class FeedStory:
    """A story entry from the fan dash feed.

    Based on /fan_dash_feed_updates response.
    Stories represent activity in the user's music feed: new releases from
    followed artists (nr), new purchases by followed fans (np), or
    featured purchases (fp).
    """

    story_type: str  # "nr" (new release), "np" (new purchase), "fp" (featured purchase)
    fan_id: int  # fan who triggered the story (your own ID for "nr")
    item_id: int  # tralbum item ID
    item_type: str  # "a" (album), "t" (track), "p" (package/merch)
    tralbum_id: int  # tralbum ID
    tralbum_type: str  # "a" or "t"
    band_id: int  # artist/band ID
    story_date: str = ""  # e.g. "13 Mar 2026 18:27:25 GMT"
    item_title: str = ""
    item_url: str = ""
    item_art_url: str | None = None
    item_art_id: int | None = None
    band_name: str = ""
    band_url: str = ""
    album_id: int | None = None
    album_title: str | None = None
    genre_id: int | None = None
    tags: list[dict[str, Any]] | None = None
    is_purchasable: bool = False
    price: float | None = None
    currency: str | None = None
    is_preorder: bool = False
    num_streamable_tracks: int | None = None
    also_collected_count: int = 0
    featured_track: int | None = None
    featured_track_title: str | None = None
    featured_track_duration: float | None = None
    featured_track_number: int | None = None
    featured_track_encodings_id: int | None = None


@dataclass
class FeedTrack:
    """A playable track from the feed's track_list.

    Each story entry has a corresponding track in track_list with streaming URL.
    """

    track_id: int
    title: str = ""
    band_id: int = 0
    band_name: str = ""
    album_id: int | None = None
    album_title: str | None = None
    track_num: int | None = None
    duration: float | None = None
    streaming_url: dict[str, str] | None = None
    art_id: int | None = None
    is_purchasable: bool = False
    price: float | None = None
    currency: str | None = None
    track_url: str | None = None


@dataclass
class FeedBandInfo:
    """Artist/band metadata from the feed's band_info lookup."""

    band_id: int
    name: str = ""
    image_id: int | None = None
    genre_id: int | None = None
    followed: int = 0


@dataclass
class FeedFanInfo:
    """Fan metadata from the feed's fan_info lookup."""

    fan_id: int
    name: str = ""
    username: str = ""
    trackpipe_url: str | None = None
    image_id: int | None = None
    collection_size: int = 0
    fav_genre_name: str | None = None


@dataclass
class FeedResponse:
    """Response from the fan_dash_feed_updates endpoint.

    Contains stories (activity entries), playable tracks, and lookup tables
    for fans and bands referenced in the stories.
    """

    stories: list[FeedStory]
    track_list: list[FeedTrack]
    fan_info: dict[str, FeedFanInfo]  # keyed by fan_id as string
    band_info: dict[str, FeedBandInfo]  # keyed by band_id as string
    oldest_story_date: int | None = None
    newest_story_date: int | None = None
    has_more: bool = False
