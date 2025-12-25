"""Tests for data models."""

from bandcamp_async_api.models import (
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


class TestSearchResultModels:
    """Test search result model classes."""

    def test_search_result_item_base(self):
        """Test base SearchResultItem."""
        item = SearchResultItem(
            type="unknown", id=123, name="Test Item", url="https://example.com"
        )
        assert item.type == "unknown"
        assert item.id == 123
        assert item.name == "Test Item"
        assert item.url == "https://example.com"

    def test_search_result_artist(self):
        """Test SearchResultArtist model."""
        artist = SearchResultArtist(
            id=123,
            name="Test Artist",
            url="https://testartist.bandcamp.com",
            location="Test City",
            is_label=False,
            tags=["electronic", "ambient"],
            image_url="https://f4.bcbits.com/img/000456_0.png",
            genre="Electronic",
        )
        assert artist.type == "artist"  # Should be set by field default
        assert artist.id == 123
        assert artist.name == "Test Artist"
        assert artist.location == "Test City"
        assert artist.is_label is False
        assert artist.tags == ["electronic", "ambient"]
        assert artist.image_url == "https://f4.bcbits.com/img/000456_0.png"
        assert artist.genre == "Electronic"

    def test_search_result_album(self):
        """Test SearchResultAlbum model."""
        album = SearchResultAlbum(
            id=789,
            name="Test Album",
            url="https://testartist.bandcamp.com/album/test-album",
            artist_id=123,
            artist_name="Test Artist",
            artist_url="https://testartist.bandcamp.com",
            image_url="https://f4.bcbits.com/img/a101112_0.png",
        )
        assert album.type == "album"  # Should be set by field default
        assert album.id == 789
        assert album.name == "Test Album"
        assert album.artist_id == 123
        assert album.artist_name == "Test Artist"
        assert album.artist_url == "https://testartist.bandcamp.com"
        assert album.image_url == "https://f4.bcbits.com/img/a101112_0.png"

    def test_search_result_track(self):
        """Test SearchResultTrack model."""
        track = SearchResultTrack(
            id=131415,
            name="Test Track",
            url="https://testartist.bandcamp.com/track/test-track",
            artist_id=123,
            artist_name="Test Artist",
            album_name="Test Album",
            album_id=789,
            artist_url="https://testartist.bandcamp.com",
            image_url="https://f4.bcbits.com/img/a101112_0.png",
        )
        assert track.type == "track"  # Should be set by field default
        assert track.id == 131415
        assert track.name == "Test Track"
        assert track.artist_id == 123
        assert track.artist_name == "Test Artist"
        assert track.album_name == "Test Album"
        assert track.album_id == 789
        assert track.artist_url == "https://testartist.bandcamp.com"
        assert track.image_url == "https://f4.bcbits.com/img/a101112_0.png"


class TestMainModels:
    """Test main data model classes."""

    def test_bc_artist(self):
        """Test BCArtist model."""
        artist = BCArtist(
            id=123,
            name="Test Artist",
            url="https://testartist.bandcamp.com",
            location="Test City, Country",
            image_url="https://f4.bcbits.com/img/000456_0.png",
            is_label=False,
            bio="Test biography",
            tags=["electronic", "ambient"],
            genre="Electronic",
        )
        assert artist.id == 123
        assert artist.name == "Test Artist"
        assert artist.url == "https://testartist.bandcamp.com"
        assert artist.location == "Test City, Country"
        assert artist.image_url == "https://f4.bcbits.com/img/000456_0.png"
        assert artist.is_label is False
        assert artist.bio == "Test biography"
        assert artist.tags == ["electronic", "ambient"]
        assert artist.genre == "Electronic"

    def test_bc_artist_defaults(self):
        """Test BCArtist with minimal fields."""
        artist = BCArtist(id=123, name="Test Artist")
        assert artist.id == 123
        assert artist.name == "Test Artist"
        assert artist.url is None
        assert artist.location is None
        assert artist.image_url is None
        assert artist.is_label is False  # Default value
        assert artist.bio is None
        assert artist.tags is None
        assert artist.genre is None

    def test_bc_album(self):
        """Test BCAlbum model."""
        artist = BCArtist(id=123, name="Test Artist")
        tracks = [
            BCTrack(id=1, title="Track 1", artist=artist),
            BCTrack(id=2, title="Track 2", artist=artist),
        ]

        album = BCAlbum(
            id=789,
            title="Test Album",
            artist=artist,
            url="https://testartist.bandcamp.com/album/test-album",
            art_url="https://f4.bcbits.com/img/a101112_0.jpg",
            release_date=1640995200,
            price={"currency": "USD", "amount": 10.0},
            is_free=False,
            is_preorder=False,
            is_purchasable=True,
            is_set_price=True,
            about="Test album description",
            credits="Test credits",
            tags=["electronic", "ambient"],
            total_tracks=10,
            tracks=tracks,
            type="album",
        )

        assert album.id == 789
        assert album.title == "Test Album"
        assert album.artist == artist
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
        assert album.tracks == tracks
        assert album.type == "album"

    def test_bc_album_defaults(self):
        """Test BCAlbum with minimal fields."""
        artist = BCArtist(id=123, name="Test Artist")

        album = BCAlbum(id=789, title="Test Album", artist=artist)

        assert album.id == 789
        assert album.title == "Test Album"
        assert album.artist == artist
        assert album.url is None
        assert album.art_url is None
        assert album.release_date is None
        assert album.price is None
        assert album.is_free is False  # Default
        assert album.is_preorder is False  # Default
        assert album.is_purchasable is False  # Default
        assert album.is_set_price is False  # Default
        assert album.about is None
        assert album.credits is None
        assert album.tags is None
        assert album.total_tracks == 0  # Default
        assert album.tracks is None
        assert album.type == "album"  # Default

    def test_bc_track(self):
        """Test BCTrack model."""
        artist = BCArtist(id=123, name="Test Artist")
        album = BCAlbum(id=789, title="Test Album", artist=artist)

        track = BCTrack(
            id=131415,
            title="Test Track",
            artist=artist,
            album=album,
            url="https://testartist.bandcamp.com/track/test-track",
            duration=180,
            streaming_url={"mp3-128": "https://example.com/track.mp3"},
            track_number=1,
            lyrics="Test lyrics",
            about="Track description",
            credits="Track credits",
            type="track",
        )

        assert track.id == 131415
        assert track.title == "Test Track"
        assert track.artist == artist
        assert track.album == album
        assert track.url == "https://testartist.bandcamp.com/track/test-track"
        assert track.duration == 180.0
        assert track.streaming_url == {"mp3-128": "https://example.com/track.mp3"}
        assert track.track_number == 1
        assert track.lyrics == "Test lyrics"
        assert track.about == "Track description"
        assert track.credits == "Track credits"
        assert track.type == "track"

    def test_bc_track_defaults(self):
        """Test BCTrack with minimal fields."""
        artist = BCArtist(id=123, name="Test Artist")

        track = BCTrack(id=131415, title="Test Track", artist=artist)

        assert track.id == 131415
        assert track.title == "Test Track"
        assert track.artist == artist
        assert track.album is None
        assert track.url is None
        assert track.duration is None
        assert track.streaming_url is None
        assert track.track_number == 0  # Default
        assert track.lyrics is None
        assert track.about is None
        assert track.credits is None
        assert track.type == "track"  # Default


class TestCollectionModels:
    """Test collection-related model classes."""

    def test_collection_item(self):
        """Test CollectionItem model."""
        item = CollectionItem(
            item_type="album",
            item_id=789,
            band_id=123,
            tralbum_type="a",
            band_name="Test Artist",
            item_title="Test Album",
            item_url="https://testartist.bandcamp.com/album/test-album",
            art_id=101112,
            num_streamable_tracks=10,
            is_purchasable=True,
            price=10.0,
        )

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
        assert item.price == 10.0

    def test_collection_item_defaults(self):
        """Test CollectionItem with minimal fields."""
        item = CollectionItem(
            item_type="album",
            item_id=789,
            band_id=123,
            band_name="Test Artist",
            item_title="Test Album",
            item_url="https://testartist.bandcamp.com/album/test-album",
        )

        assert item.item_type == "album"
        assert item.item_id == 789
        assert item.band_id == 123
        assert item.tralbum_type is None
        assert item.band_name == "Test Artist"
        assert item.item_title == "Test Album"
        assert item.item_url == "https://testartist.bandcamp.com/album/test-album"
        assert item.art_id is None
        assert item.num_streamable_tracks is None
        assert item.is_purchasable is False  # Default
        assert item.price is None

    def test_collection_summary(self):
        """Test CollectionSummary model."""
        items = [
            CollectionItem(
                item_type="album",
                item_id=789,
                band_id=123,
                band_name="Test Artist",
                item_title="Test Album",
                item_url="https://testartist.bandcamp.com/album/test-album",
            )
        ]

        summary = CollectionSummary(
            fan_id=999, items=items, has_more=False, last_token="token123"
        )

        assert summary.fan_id == 999
        assert summary.items == items
        assert summary.has_more is False
        assert summary.last_token == "token123"

    def test_collection_summary_defaults(self):
        """Test CollectionSummary with minimal fields."""
        summary = CollectionSummary(fan_id=999, items=[])

        assert summary.fan_id == 999
        assert summary.items == []
        assert summary.has_more is False  # Default
        assert summary.last_token is None
