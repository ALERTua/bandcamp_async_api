"""Tests for BandcampParsers."""

import pytest

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

        result = parsers.parse_search_result_item(data)

        assert result.type == "artist"
        assert result.id == 123
        assert result.name == "Test Artist"
        assert result.url == "https://testartist.bandcamp.com"
        assert result.location == "Test City"
        assert result.is_label is False
        assert result.tags == ["electronic", "ambient"]
        assert result.image_url == "https://f4.bcbits.com/img/000456_0.png"
        assert result.genre == "Electronic"

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

        result = parsers.parse_search_result_item(data)

        assert result.type == "album"
        assert result.id == 789
        assert result.name == "Test Album"
        assert result.url == "https://testartist.bandcamp.com/album/test-album"
        assert result.artist_id == 123
        assert result.artist_name == "Test Artist"
        assert result.artist_url == "https://testartist.bandcamp.com"
        assert result.image_url == "https://f4.bcbits.com/img/a101112_0.png"

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

        result = parsers.parse_search_result_item(data)

        assert result.type == "track"
        assert result.id == 131415
        assert result.name == "Test Track"
        assert result.url == "https://testartist.bandcamp.com/track/test-track"
        assert result.artist_id == 123
        assert result.artist_name == "Test Artist"
        assert result.album_name == "Test Album"
        assert result.album_id == 789
        assert result.artist_url == "https://testartist.bandcamp.com"
        assert result.image_url == "https://f4.bcbits.com/img/a101112_0.png"

    def test_parse_search_result_item_unknown_type(self, parsers):
        """Test parsing unknown search result type."""
        data = {
            "type": "x",
            "id": 999,
            "name": "Unknown Item",
            "url": "https://example.com",
        }
        result = parsers.parse_search_result_item(data)
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

        artist = parsers.parse_artist(data)

        assert artist.id == 123
        assert artist.name == "Test Artist"
        assert artist.url == "https://testartist.bandcamp.com"
        assert artist.location == "Test City, Country"
        assert artist.image_url == "https://f4.bcbits.com/img/000456_0.png"
        assert artist.is_label is False
        assert artist.bio == "Test artist biography"
        assert artist.tags == ["electronic", "ambient"]
        assert artist.genre == "Electronic"

    def test_parse_album(self, parsers):
        """Test parsing album data."""
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

        assert album.id == 789
        assert album.title == "Test Album"
        assert album.artist.name == "Test Artist"
        assert album.url == "https://testartist.bandcamp.com/album/test-album"
        assert album.art_url == "https://f4.bcbits.com/img/a101112_0.jpg"
        assert album.release_date == 1640995200
        assert album.price == {"currency": "USD", "amount": 10.0}
        assert album.is_free is False
        assert album.is_preorder is False
        assert album.is_purchasable is True
        assert album.is_set_price is True
        assert album.about == "Test album description"
        assert album.credits == "Test credits"
        assert album.tags == ["electronic", "ambient"]
        assert album.total_tracks == 10
        assert len(album.tracks) == 2
        assert album.tracks[0].title == "Test Track 1"
        assert album.tracks[1].title == "Test Track 2"
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

        assert track.id == 131415
        assert track.title == "Test Track"
        assert track.artist.name == "Test Artist"
        assert track.album is None  # Single tracks don't have album context
        assert track.url == "https://testartist.bandcamp.com/track/test-track"
        assert track.duration == 180
        assert track.streaming_url == {"mp3-128": "https://example.com/track.mp3"}
        assert track.track_number == 1
        assert track.lyrics == "Test lyrics"
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

        assert item.item_type == "album"
        assert item.item_id == 789
        assert item.band_id == 123
        assert item.tralbum_type == "a"
        assert item.band_name == "Test Artist"
        assert item.item_title == "Test Album"
        assert item.item_url == "https://testartist.bandcamp.com/album/test-album"
        assert item.art_id == 101112
        assert item.num_streamable_tracks == 10
        assert item.is_purchasable is True
        assert item.price == {"currency": "USD", "amount": 10.0}

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
        assert price_info == {"currency": "USD", "amount": 15.99}

    def test_parse_price_info_missing(self, parsers):
        """Test parsing price info when fields are missing."""
        data = {}

        price_info = parsers._parse_price_info(data)
        assert price_info is None

    def test_build_art_url_album(self, parsers):
        """Test building art URL for album."""
        url = parsers._build_art_url(12345, "album")
        assert url == "https://f4.bcbits.com/img/a12345_0.jpg"

    def test_build_art_url_artist(self, parsers):
        """Test building art URL for artist."""
        url = parsers._build_art_url(12345, "artist")
        assert url == "https://f4.bcbits.com/img/00012345_0.png"

    def test_build_art_url_none(self, parsers):
        """Test building art URL with None art_id."""
        url = parsers._build_art_url(None, "album")
        assert url is None

    def test_parse_artist_from_album(self, parsers):
        """Test parsing artist info from album data."""
        data = {
            "band": {"band_id": 123, "name": "Test Artist", "location": "Test City"},
            "tralbum_artist": "Test Artist",
        }

        artist = parsers._parse_artist_from_album(data)

        assert artist.id == 123
        assert artist.name == "Test Artist"
        assert artist.location == "Test City"

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

        assert track.id == 131415
        assert track.title == "Test Track"
        assert track.artist == album.artist
        assert track.album == album
        assert track.duration == 180
        assert track.track_number == 1
