"""Tests for BandcampParsers."""

import pytest

from bandcamp_async_api import (
    SearchResultTrack,
    SearchResultArtist,
    SearchResultAlbum,
    BCArtist,
)
from bandcamp_async_api.parsers import BandcampParsers


class TestBandcampParsers:
    """Test BandcampParsers functionality."""

    @pytest.fixture
    def parsers(self):
        """Create a BandcampParsers instance."""
        return BandcampParsers()

    def test_parse_search_result_item_artist(self, parsers):
        """Test parsing artist search result."""
        data = {
            "type": "b",
            "id": 123,
            "name": "Test Artist",
            "url": "https://testartist.bandcamp.com",
            "location": "Test City",
            "is_label": False,
            "tag_names": ["electronic", "ambient"],
            "img_id": 456,
            "genre_name": "Electronic",
        }

        # noinspection PyTypeChecker
        result: SearchResultArtist = parsers.parse_search_result_item(data)

        assert result.type == "artist"
        assert result.id == data['id']
        assert result.name == data['name']
        assert result.url == data['url']
        assert result.location == data['location']
        assert result.is_label is data['is_label']
        assert result.tags == data['tag_names']
        assert (
            result.image_url == f"https://f4.bcbits.com/img/000{data['img_id']}_0.png"
        )
        assert result.genre == data['genre_name']

    def test_parse_search_result_item_album(self, parsers):
        """Test parsing album search result."""
        data = {
            "type": "a",
            "id": 789,
            "name": "Test Album",
            "url": "https://testartist.bandcamp.comhttps://testartist.bandcamp.com/album/test-album",
            "band_id": 123,
            "band_name": "Test Artist",
            "art_id": 101112,
        }

        # noinspection PyTypeChecker,DuplicatedCode
        result: SearchResultAlbum = parsers.parse_search_result_item(data)

        assert result.type == "album"
        assert result.id == data['id']
        assert result.name == data['name']
        assert result.url == "https://testartist.bandcamp.com/album/test-album"
        assert result.artist_id == data['band_id']
        assert result.artist_name == data['band_name']
        assert result.artist_url == "https://testartist.bandcamp.com"
        assert result.image_url == f"https://f4.bcbits.com/img/a{data['art_id']}_0.png"

    def test_parse_search_result_item_track(self, parsers):
        """Test parsing track search result."""
        data = {
            "type": "t",
            "id": 131415,
            "name": "Test Track",
            "url": "https://testartist.bandcamp.comhttps://testartist.bandcamp.com/track/test-track",
            "band_id": 123,
            "band_name": "Test Artist",
            "album_name": "Test Album",
            "album_id": 789,
            "art_id": 101112,
        }

        # noinspection PyTypeChecker,DuplicatedCode
        result: SearchResultTrack = parsers.parse_search_result_item(data)

        assert result.type == "track"
        assert result.id == data['id']
        assert result.name == data['name']
        assert result.url == "https://testartist.bandcamp.com/track/test-track"
        assert result.artist_id == data['band_id']
        assert result.artist_name == data['band_name']
        assert result.album_name == data['album_name']
        assert result.album_id == data['album_id']
        assert result.artist_url == "https://testartist.bandcamp.com"
        assert result.image_url == f"https://f4.bcbits.com/img/a{data['art_id']}_0.png"

    def test_parse_search_result_item_unknown_type(self, parsers):
        """Test parsing unknown search result type."""
        data = {
            "type": "x",
            "id": 999,
            "name": "Unknown Item",
            "url": "https://example.com",
        }
        result: None = parsers.parse_search_result_item(data)
        assert result is None

    def test_parse_artist(self, parsers):
        """Test parsing artist data."""
        data = {
            "id": 123,
            "name": "Test Artist",
            "bandcamp_url": "https://testartist.bandcamp.com",
            "location_text": "Test City, Country",
            "bio_image_id": 456,
            "bio": "Test artist biography",
            "tags": [{"name": "electronic"}, {"name": "ambient"}],
            "genre_name": "Electronic",
            "band": {"is_label": False},
        }

        artist: BCArtist = parsers.parse_artist(data)

        assert artist.id == data['id']
        assert artist.name == data['name']
        assert artist.url == data['bandcamp_url']
        assert artist.location == data['location_text']
        assert (
            artist.image_url
            == f"https://f4.bcbits.com/img/000{data['bio_image_id']}_0.png"
        )
        assert artist.is_label is data['band']['is_label']  # ty:ignore[invalid-argument-type, non-subscriptable]
        assert artist.bio == data['bio']
        assert artist.tags == [tag['name'] for tag in data['tags']]  # ty:ignore[non-subscriptable, not-iterable, invalid-argument-type]
        assert artist.genre == data['genre_name']

    def test_parse_album(self, parsers):
        """Test parsing album data."""
        # noinspection DuplicatedCode
        data = {
            "id": 789,
            "title": "Test Album",
            "bandcamp_url": "https://testartist.bandcamp.com/album/test-album",
            "art_id": 101112,
            "release_date": 1640995200,
            "price": 10.0,
            "currency": "USD",
            "is_preorder": False,
            "is_purchasable": True,
            "is_set_price": True,
            "about": "Test album description",
            "credits": "Test credits",
            "tags": [{"name": "electronic"}, {"name": "ambient"}],
            "num_downloadable_tracks": 10,
            "tracks": [
                {
                    "track_id": 131415,
                    "title": "Test Track 1",
                    "duration": 180,
                    "track_num": 1,
                    "streaming_url": {"mp3-128": "https://example.com/track1.mp3"},
                    "lyrics": "Test lyrics",
                    "is_streamable": True,
                },
                {
                    "track_id": 161718,
                    "title": "Test Track 2",
                    "duration": 200,
                    "track_num": 2,
                    "streaming_url": {"mp3-128": "https://example.com/track2.mp3"},
                    "is_streamable": True,
                },
            ],
            "band": {"band_id": 123, "name": "Test Artist", "location": "Test City"},
            "tralbum_artist": "Test Artist",
        }

        album = parsers.parse_album(data)

        assert album.id == data['id']
        assert album.title == data['title']
        assert album.artist.name == data['tralbum_artist']
        assert album.url == data['bandcamp_url']
        assert album.art_url == f"https://f4.bcbits.com/img/a{data['art_id']}_0.jpg"
        assert album.release_date == data['release_date']
        assert album.price == {"currency": data['currency'], "amount": data['price']}
        assert album.is_free is (data['price'] == 0)
        assert album.is_preorder is data['is_preorder']
        assert album.is_purchasable is data['is_purchasable']
        assert album.is_set_price is data['is_set_price']
        assert album.about == data['about']
        assert album.credits == data['credits']
        # noinspection PyTypeChecker
        assert album.tags == [tag['name'] for tag in data['tags']]  # ty:ignore[non-subscriptable, invalid-argument-type, not-iterable]
        assert album.total_tracks == data['num_downloadable_tracks']
        assert len(album.tracks) == len(data['tracks'])  # ty:ignore[invalid-argument-type]
        # noinspection PyTypeChecker
        assert album.tracks[0].title == data['tracks'][0]['title']  # ty:ignore[non-subscriptable, invalid-argument-type]
        # noinspection PyTypeChecker
        assert album.tracks[1].title == data['tracks'][1]['title']  # ty:ignore[non-subscriptable, invalid-argument-type]
        assert album.type == "album"

    def test_parse_track(self, parsers):
        """Test parsing track data."""
        data = {
            "id": 131415,
            "title": "Test Track",
            "bandcamp_url": "https://testartist.bandcamp.com/track/test-track",
            "tracks": [
                {
                    "title": "Test Track",
                    "duration": 180,
                    "track_num": 1,
                    "streaming_url": {"mp3-128": "https://example.com/track.mp3"},
                    "lyrics": "Test lyrics",
                }
            ],
            "band": {"band_id": 123, "name": "Test Artist"},
            "tralbum_artist": "Test Artist",
        }

        track = parsers.parse_track(data)

        assert track.id == data['id']
        assert track.title == data['title']
        assert track.artist.name == data['tralbum_artist']
        assert track.album is None  # Single tracks don't have album context
        assert track.url == data['bandcamp_url']
        assert track.duration == data['tracks'][0]['duration']  # ty:ignore[non-subscriptable, invalid-argument-type]
        assert track.streaming_url == data['tracks'][0]['streaming_url']  # ty:ignore[non-subscriptable, invalid-argument-type]
        assert track.track_number == data['tracks'][0]['track_num']  # ty:ignore[non-subscriptable, invalid-argument-type]
        assert track.lyrics == data['tracks'][0]['lyrics']  # ty:ignore[non-subscriptable, non-subscriptable, invalid-argument-type]
        assert track.type == "track"

    def test_parse_collection_item(self, parsers):
        """Test parsing collection item data."""
        data = {
            "item_type": "album",
            "item_id": 789,
            "band_id": 123,
            "tralbum_type": "a",
            "band_name": "Test Artist",
            "item_title": "Test Album",
            "item_url": "https://testartist.bandcamp.com/album/test-album",
            "art_id": 101112,
            "num_streamable_tracks": 10,
            "is_purchasable": True,
            "price": {"currency": "USD", "amount": 10.0},
        }

        item = parsers.parse_collection_item(data)

        assert item.item_type == data['item_type']
        assert item.item_id == data['item_id']
        assert item.band_id == data['band_id']
        assert item.tralbum_type == data['tralbum_type']
        assert item.band_name == data['band_name']
        assert item.item_title == data['item_title']
        assert item.item_url == data['item_url']
        assert item.art_id == data['art_id']
        assert item.num_streamable_tracks == data['num_streamable_tracks']
        assert item.is_purchasable is data['is_purchasable']
        assert item.price == data['price']

    def test_parse_bandcamp_urls(self, parsers):
        """Test parsing Bandcamp URL format."""
        raw_url = (
            "https://artist.bandcamp.comhttps://artist.bandcamp.com/album/album-name"
        )

        artist_url, item_url = parsers._parse_bandcamp_urls(raw_url)

        assert artist_url == "https://artist.bandcamp.com"
        assert item_url == "https://artist.bandcamp.com/album/album-name"

    def test_determine_album_type_album(self, parsers):
        """Test determining album type for regular album."""
        data = {
            "tracks": [
                {"track_id": 1, "is_streamable": True},
                {"track_id": 2, "is_streamable": True},
            ]
        }

        album_type = parsers._determine_album_type(data, is_single_track=False)
        assert album_type == "album"

    def test_determine_album_type_single_track(self, parsers):
        """Test determining album type for single track."""
        data = {"tracks": [{"track_id": 789, "is_streamable": True}], "id": 789}

        album_type = parsers._determine_album_type(data, is_single_track=True)
        assert album_type == "track"

    def test_determine_album_type_album_single(self, parsers):
        """Test determining album type for album-single."""
        data = {
            "item_type": "track",
            "tracks": [{"track_id": 1, "is_streamable": True}],
        }

        album_type = parsers._determine_album_type(data, is_single_track=False)
        assert album_type == "album-single"

    def test_parse_price_info(self, parsers):
        """Test parsing price information."""
        data = {"currency": "USD", "price": 15.99}

        price_info = parsers._parse_price_info(data)
        assert price_info == {"currency": data['currency'], "amount": data['price']}

    def test_parse_price_info_missing(self, parsers):
        """Test parsing price info when fields are missing."""
        data = {}

        price_info = parsers._parse_price_info(data)
        assert price_info is None

    def test_build_art_url_album(self, parsers):
        """Test building art URL for album."""
        art_id = 12345
        expected_url = f"https://f4.bcbits.com/img/a{art_id}_0.jpg"

        url = parsers._build_art_url(art_id, "album")
        assert url == expected_url

    def test_build_art_url_artist(self, parsers):
        """Test building art URL for artist."""
        art_id = 12345
        expected_url = f"https://f4.bcbits.com/img/000{art_id}_0.png"

        url = parsers._build_art_url(art_id, "artist")
        assert url == expected_url

    def test_build_art_url_none(self, parsers):
        """Test building art URL with None art_id."""
        art_id = None

        url = parsers._build_art_url(art_id, "album")
        assert url is None

    def test_parse_artist_from_album(self, parsers):
        """Test parsing artist info from album data."""
        data = {
            "band": {"band_id": 123, "name": "Test Artist", "location": "Test City"},
            "tralbum_artist": "Test Artist",
        }

        artist = parsers._parse_artist_from_album(data)

        assert artist.id == data['band']['band_id']  # ty:ignore[invalid-argument-type]
        assert artist.name == data['tralbum_artist']
        assert artist.location == data['band']['location']  # ty:ignore[invalid-argument-type]

    def test_parse_track_from_album(self, parsers):
        """Test parsing track from album context."""
        album = parsers.parse_album(
            {
                "id": 789,
                "title": "Test Album",
                "band": {"band_id": 123, "name": "Test Artist"},
                "tralbum_artist": "Test Artist",
            }
        )

        track_data = {
            "track_id": 131415,
            "title": "Test Track",
            "duration": 180,
            "track_num": 1,
            "streaming_url": {"mp3-128": "https://example.com/track.mp3"},
        }

        track = parsers._parse_track_from_album(track_data, album)

        assert track.id == track_data['track_id']
        assert track.title == track_data['title']
        assert track.artist == album.artist
        assert track.album == album
        assert track.duration == track_data['duration']
        assert track.track_number == track_data['track_num']
