"""Bandcamp API response parsers."""

import re
from typing import Any

from .models import (
    BCAlbum,
    BCArtist,
    BCTrack,
    CollectionItem,
    FanItem,
    FeedBandInfo,
    FeedFanInfo,
    FeedResponse,
    FeedStory,
    FeedTrack,
    FollowingItem,
    SearchResultAlbum,
    SearchResultArtist,
    SearchResultItem,
    SearchResultTrack,
)


_SUBDOMAIN_RE = re.compile(r"^[a-zA-Z0-9-]+$")


class BandcampParsers:
    """Parsers for Bandcamp API responses to model objects."""

    @staticmethod
    def _build_image_url(image_id: Any) -> str | None:
        """Build image URL from image_id."""
        if not isinstance(image_id, int):
            return None
        return f"https://f4.bcbits.com/img/{image_id}_0.jpg"

    def parse_search_result_item(self, data: dict[str, Any]) -> SearchResultItem | None:
        """Parse search result item from API response."""
        item_type = data.get("type")

        if item_type == "b":  # Band/artist
            return SearchResultArtist(
                id=data["id"],
                name=data["name"],
                url=data["url"],
                location=data.get("location"),
                is_label=data.get("is_label", False),
                tags=data.get("tag_names", []),
                image_url=f"https://f4.bcbits.com/img/000{data.get('img_id', 0)}_0.png",
                genre=data.get("genre_name"),
            )

        elif item_type == "a":  # Album
            artist_url, album_url = self._parse_bandcamp_urls(data["url"])
            # `img` field url leads to 404
            return SearchResultAlbum(
                id=data["id"],
                name=data["name"],
                url=album_url,
                artist_id=data["band_id"],
                artist_name=data["band_name"],
                artist_url=artist_url,
                image_url=f"https://f4.bcbits.com/img/a{data.get('art_id', 0)}_0.png",
                tags=data.get("tag_names", []),
            )

        elif item_type == "t":  # Track
            artist_url, track_url = self._parse_bandcamp_urls(data["url"])
            # `img` field url leads to 404
            return SearchResultTrack(
                id=data["id"],
                name=data["name"],
                url=track_url,
                artist_id=data["band_id"],
                artist_name=data["band_name"],
                album_name=data.get("album_name", ""),
                album_id=data.get("album_id"),
                artist_url=artist_url,
                image_url=f"https://f4.bcbits.com/img/a{data.get('art_id', 0)}_0.png",
            )

        return None

    def parse_artist(self, data: dict[str, Any]) -> BCArtist:
        """Parse artist data from API response."""
        band_data = data.get("band", data)

        return BCArtist(
            id=data["id"],
            name=data["name"],
            url=data["bandcamp_url"],
            location=data.get("location_text"),
            image_url=(
                f"https://f4.bcbits.com/img/000{data.get('bio_image_id', 0)}_0.png"
                if data.get("bio_image_id")
                else None
            ),
            is_label=band_data.get("is_label", False),
            bio=data.get("bio"),
            tags=[tag["name"] for tag in data.get("tags", [])],
            genre=data.get("genre_name"),
        )

    def parse_album(self, data: dict[str, Any]) -> BCAlbum:
        """Parse album data from API response."""
        # Handle both album and track responses
        is_single_track = (
            data.get("tracks")
            and len(data["tracks"]) == 1
            and data["tracks"][0].get("track_id") == data.get("id")
        )

        album_type = self._determine_album_type(data, is_single_track)  # ty:ignore[invalid-argument-type]

        # Parse artist
        artist = self._parse_artist_from_album(data)

        # Parse price info
        price_info = self._parse_price_info(data)

        album = BCAlbum(
            id=data["id"],
            title=data.get("title", data.get("album_title", "Unknown")),
            artist=artist,
            url=data.get("bandcamp_url"),
            art_url=self._build_art_url(data.get("art_id"), "album"),
            release_date=data.get("release_date"),
            price=price_info,
            is_free=data.get("price", 0) == 0,
            is_preorder=data.get("is_preorder", False),
            is_purchasable=data.get("is_purchasable", False),
            is_set_price=data.get("is_set_price", False),
            about=data.get("about"),
            credits=data.get("credits"),
            tags=[tag["name"] for tag in data.get("tags", [])],
            total_tracks=data.get("num_downloadable_tracks", 0),
            type=album_type,
            # The per-album performer credit, when the API set it.
            # Compare against `artist.name` (the page owner) to detect
            # label-released albums.
            tralbum_artist=data.get("tralbum_artist"),
        )

        # Parse tracks if available
        if "tracks" in data:
            album.tracks = []
            for track_data in data["tracks"]:
                if track_data.get("is_streamable", True):
                    track = self._parse_track_from_album(track_data, album)
                    album.tracks.append(track)

        return album

    def parse_track(self, data: dict[str, Any]) -> BCTrack:
        """Parse track data from API response."""
        # For single tracks, the data structure is similar to albums
        artist = self._parse_artist_from_album(data)

        track_data = data.get("tracks", [{}])[0] if data.get("tracks") else data

        return BCTrack(
            id=data["id"],
            title=data.get("title", track_data.get("title", "Unknown")),
            artist=artist,
            album=None,  # Single tracks don't have album context
            url=data.get("bandcamp_url"),
            duration=track_data.get("duration"),
            streaming_url=track_data.get("streaming_url"),
            track_number=track_data.get("track_num", 0) or 0,
            lyrics=track_data.get("lyrics"),
            about=data.get("about"),
            credits=data.get("credits"),
            tralbum_artist=data.get("tralbum_artist"),
        )

    def parse_collection_item(self, data: dict[str, Any]) -> CollectionItem:
        """Parse collection item from API response."""
        # Extract price as float from dict or use directly if already float
        return CollectionItem(
            item_type=data.get("item_type", ""),
            item_id=data["item_id"],
            band_id=data["band_id"],
            tralbum_type=data.get("tralbum_type"),
            band_name=data.get("band_name", ""),
            item_title=data.get("item_title", ""),
            item_url=data.get("item_url", ""),
            art_id=data.get("art_id"),
            num_streamable_tracks=data.get("num_streamable_tracks"),
            is_purchasable=data.get("is_purchasable", False),
            price=data.get("price"),
            token=data.get("token"),
        )

    def parse_following_item(self, data: dict[str, Any]) -> FollowingItem:
        """Parse a followed band/artist from the following_bands API response."""
        band_id = data.get("band_id")
        if band_id is None:
            raise ValueError(
                f"Missing required field 'band_id' in following item: {data}"
            )

        url_hints = data.get("url_hints", {})
        subdomain = url_hints.get("subdomain") if url_hints else None
        if subdomain and not _SUBDOMAIN_RE.match(subdomain):
            subdomain = None
        url = f"https://{subdomain}.bandcamp.com" if subdomain else None

        return FollowingItem(
            band_id=band_id,
            name=data.get("name", ""),
            url=url,
            image_url=self._build_image_url(data.get("image_id")),
            location=data.get("location"),
            date_followed=data.get("date_followed"),
            is_label=data.get("is_label", False),
            token=data.get("token"),
        )

    def parse_fan_item(self, data: dict[str, Any]) -> FanItem:
        """Parse a fan/user from the following_fans or followers API response."""
        fan_id = data.get("fan_id")
        if fan_id is None:
            raise ValueError(f"Missing required field 'fan_id' in fan item: {data}")

        return FanItem(
            fan_id=fan_id,
            name=data.get("name", ""),
            url=data.get("trackpipe_url"),
            image_url=self._build_image_url(data.get("image_id")),
            location=data.get("location"),
            date_followed=data.get("date_followed"),
            is_following=data.get("is_following", False),
            token=data.get("token"),
        )

    def _parse_artist_from_album(self, data: dict[str, Any]) -> BCArtist:
        """Parse the page-owning band from an album/track response.

        BCArtist always represents the Bandcamp page owner — never a
        per-album performer credit. For label-released albums the
        performer name lives on `BCAlbum.tralbum_artist` instead, since
        the performer typically has no Bandcamp page of their own.
        """
        band_data = data.get("band", {})

        return BCArtist(
            id=band_data.get("band_id", data.get("band_id", 0)),
            name=band_data.get("name", "Unknown"),
            url=(
                data.get("bandcamp_url", "").split("/album")[0]
                if data.get("bandcamp_url")
                else None
            ),
            location=band_data.get("location"),
            image_url=(
                f"https://f4.bcbits.com/img/000{band_data.get('image_id', 0)}_0.png"
                if band_data.get("image_id")
                else None
            ),
            is_label=band_data.get("is_label", False),
        )

    def _parse_track_from_album(
        self, track_data: dict[str, Any], album: BCAlbum
    ) -> BCTrack:
        """Parse track data from within album context."""
        return BCTrack(
            id=track_data["track_id"],
            title=track_data["title"],
            artist=album.artist,
            album=album,
            url=album.url,
            duration=track_data.get("duration"),
            streaming_url=track_data.get("streaming_url"),
            track_number=track_data.get("track_num", 0) or 0,
            lyrics=track_data.get("lyrics"),
        )

    def _parse_bandcamp_urls(self, raw_url: str) -> tuple[str, str]:
        """Parse Bandcamp's weird URL format into artist and item URLs.

        Bandcamp returns URLs like:
        "https://artist.bandcamp.comhttps://artist.bandcamp.com/album/album-name"

        This parses it into separate artist and item URLs.
        """
        url_parts = raw_url.split("https")
        artist_url = "https" + url_parts[1]
        item_url = "https" + url_parts[2]
        return artist_url, item_url

    def _determine_album_type(self, data: dict[str, Any], is_single_track: bool) -> str:
        """Determine the album type based on data."""
        if is_single_track:
            return "track"
        if data.get("item_type") == "track":
            return "album-single"
        return "album"

    def _parse_price_info(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Parse price information from API data."""
        if "currency" in data and "price" in data:
            return {"currency": data["currency"], "amount": data["price"]}
        return None

    def parse_feed_story(self, data: dict[str, Any]) -> FeedStory:
        """Parse a story entry from the fan dash feed response."""
        return FeedStory(
            story_type=data.get("story_type", ""),
            fan_id=data["fan_id"],
            item_id=data["item_id"],
            item_type=data.get("item_type", ""),
            tralbum_id=data.get("tralbum_id", data["item_id"]),
            tralbum_type=data.get("tralbum_type", ""),
            band_id=data.get("band_id", 0),
            story_date=data.get("story_date", ""),
            item_title=data.get("item_title", ""),
            item_url=data.get("item_url", ""),
            item_art_url=data.get("item_art_url"),
            item_art_id=data.get("item_art_id"),
            band_name=data.get("band_name", ""),
            band_url=data.get("band_url", ""),
            album_id=data.get("album_id"),
            album_title=data.get("album_title"),
            genre_id=data.get("genre_id"),
            tags=data.get("tags"),
            is_purchasable=data.get("is_purchasable", False),
            price=data.get("price"),
            currency=data.get("currency"),
            is_preorder=data.get("is_preorder", False),
            num_streamable_tracks=data.get("num_streamable_tracks"),
            also_collected_count=data.get("also_collected_count", 0),
            featured_track=data.get("featured_track"),
            featured_track_title=data.get("featured_track_title"),
            featured_track_duration=data.get("featured_track_duration"),
            featured_track_number=data.get("featured_track_number"),
            featured_track_encodings_id=data.get("featured_track_encodings_id"),
        )

    def parse_feed_track(self, data: dict[str, Any]) -> FeedTrack:
        """Parse a track entry from the feed's track_list."""
        return FeedTrack(
            track_id=data["track_id"],
            title=data.get("title", ""),
            band_id=data.get("band_id", 0),
            band_name=data.get("band_name", ""),
            album_id=data.get("album_id"),
            album_title=data.get("album_title"),
            track_num=data.get("track_num"),
            duration=data.get("duration"),
            streaming_url=data.get("streaming_url"),
            art_id=data.get("art_id"),
            is_purchasable=data.get("is_purchasable", False),
            price=data.get("price"),
            currency=data.get("currency"),
            track_url=data.get("track_url"),
        )

    def parse_feed_band_info(self, data: dict[str, Any]) -> FeedBandInfo:
        """Parse a band_info entry from the feed response."""
        return FeedBandInfo(
            band_id=data.get("band_id", 0),
            name=data.get("name", ""),
            image_id=data.get("image_id"),
            genre_id=data.get("genre_id"),
            followed=data.get("followed", 0),
        )

    def parse_feed_fan_info(self, data: dict[str, Any]) -> FeedFanInfo:
        """Parse a fan_info entry from the feed response."""
        return FeedFanInfo(
            fan_id=data.get("fan_id", 0),
            name=data.get("name", ""),
            username=data.get("username", ""),
            trackpipe_url=data.get("trackpipe_url"),
            image_id=data.get("image_id"),
            collection_size=data.get("collection_size", 0),
            fav_genre_name=data.get("fav_genre_name"),
        )

    def parse_feed_response(self, data: dict[str, Any]) -> FeedResponse:
        """Parse the full fan_dash_feed_updates response."""
        stories_data = data.get("stories", {})
        entries = stories_data.get("entries", [])
        track_list_data = stories_data.get("track_list", [])

        stories = [self.parse_feed_story(e) for e in entries]
        track_list = [self.parse_feed_track(t) for t in track_list_data]

        fan_info = {
            k: self.parse_feed_fan_info(v) for k, v in data.get("fan_info", {}).items()
        }
        band_info = {
            k: self.parse_feed_band_info(v)
            for k, v in data.get("band_info", {}).items()
        }

        oldest = stories_data.get("oldest_story_date")
        newest = stories_data.get("newest_story_date")
        # If we got stories and there's an oldest date, there's likely more
        has_more = bool(oldest and len(stories) > 0)

        return FeedResponse(
            stories=stories,
            track_list=track_list,
            fan_info=fan_info,
            band_info=band_info,
            oldest_story_date=oldest,
            newest_story_date=newest,
            has_more=has_more,
        )

    def _build_art_url(self, art_id: int | None, item_type: str) -> str | None:
        """Build artwork URL from art_id and item type."""
        if not art_id:
            return None

        if item_type == "album":
            return f"https://f4.bcbits.com/img/a{art_id}_0.jpg"
        elif item_type == "artist":
            return f"https://f4.bcbits.com/img/000{art_id}_0.png"
        else:
            return f"https://f4.bcbits.com/img/a{art_id}_0.png"
