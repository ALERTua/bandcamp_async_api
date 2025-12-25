"""Real data tests for main Bandcamp API methods.

These tests require BANDCAMP_IDENTITY_TOKEN environment variable to be set.
Tests are marked as manual and should be run explicitly with:
    pytest -m manual tests/real_data/

Run with: pytest -m manual tests/real_data/test_main_api.py -v
"""

import logging
import pytest

from bandcamp_async_api.client import BandcampAPIError, BandcampNotFoundError
from bandcamp_async_api.models import BCArtist, BCAlbum, BCTrack

from .constants import (
    TEST_ARTIST_NAME,
    TEST_ALBUM_NAME,
    TEST_TRACK_NAME,
    TEST_ARTIST_URL,
    TEST_ARTIST_ID,
    TEST_ALBUM_ID,
    TEST_TRACK_ID,
)

logger = logging.getLogger(__name__)


# Manual test marker
manual = pytest.mark.manual


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_search_artist(bc_api_client):
    """Test searching for Pathos artist."""
    results = await bc_api_client.search(TEST_ARTIST_NAME)

    # Find artist result
    artist_results = [r for r in results if r.type == "artist"]
    assert len(artist_results) > 0, f"No artist results found for '{TEST_ARTIST_NAME}'"

    pathos_result = next(
        (r for r in artist_results if TEST_ARTIST_NAME.lower() in r.name.lower()), None
    )
    assert pathos_result is not None, (
        f"Pathos not found in search results for '{TEST_ARTIST_NAME}'"
    )

    assert pathos_result.id > 0, "Invalid artist ID retrieved"
    logger.info(f"Found artist: {pathos_result.name} (ID: {pathos_result.id})")


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_search_album(bc_api_client):
    """Test searching for Rapture album."""
    results = await bc_api_client.search(TEST_ALBUM_NAME)

    # Find album result
    album_results = [r for r in results if r.type == "album"]
    assert len(album_results) > 0, f"No album results found for '{TEST_ALBUM_NAME}'"

    album_result = next(
        (
            r
            for r in album_results
            if TEST_ALBUM_NAME.lower() == r.name.lower()
            and TEST_ARTIST_NAME.lower() == r.artist_name.lower()
        ),
        None,
    )
    assert album_result is not None, (
        f"Album not found in search results for '{TEST_ALBUM_NAME}'"
    )

    assert album_result.id > 0, "Invalid album ID retrieved"
    logger.info(f"Found album: {album_result.name} (ID: {album_result.id})")


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_search_track(bc_api_client):
    """Test searching for I Don't Dream With Gods track."""
    results = await bc_api_client.search(TEST_TRACK_NAME)

    # Find track result
    track_results = [r for r in results if r.type == "track"]
    assert len(track_results) > 0, f"No track results found for '{TEST_TRACK_NAME}'"

    track_result = next(
        (r for r in track_results if TEST_TRACK_NAME.lower() in r.name.lower()), None
    )
    assert track_result is not None, (
        f"Test track not found in search results for '{TEST_TRACK_NAME}'"
    )

    assert track_result.id > 0, "Invalid track ID retrieved"
    logger.info(f"Found track: {track_result.name} (ID: {track_result.id})")

    # Validate it belongs to Pathos
    assert TEST_ARTIST_NAME.lower() in track_result.artist_name.lower()


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_get_artist_details(bc_api_client):
    """Test getting detailed artist information."""
    artist = await bc_api_client.get_artist(TEST_ARTIST_ID)

    assert isinstance(artist, BCArtist), f"Expected BCArtist, got {type(artist)}"
    assert artist.id == TEST_ARTIST_ID, "Artist ID mismatch"
    assert artist.name == TEST_ARTIST_NAME, "Artist name mismatch"
    assert artist.url is not None, "Artist URL should not be None"
    assert TEST_ARTIST_URL == artist.url, f"Artist URL should contain {TEST_ARTIST_URL}"

    logger.info(f"Artist details: {artist.name}")
    logger.debug(f"Location: {artist.location}")
    logger.debug(f"Bio: {artist.bio[:100] if artist.bio else 'None'}...")
    logger.debug(f"Tags: {artist.tags}")


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_get_album_details(bc_api_client):
    """Test getting detailed album information."""
    album = await bc_api_client.get_album(TEST_ARTIST_ID, TEST_ALBUM_ID)

    assert isinstance(album, BCAlbum), f"Expected BCAlbum, got {type(album)}"
    assert album.id == TEST_ALBUM_ID, "Album ID mismatch"
    assert album.title == TEST_ALBUM_NAME, "Album title mismatch"
    assert album.artist.id == TEST_ARTIST_ID, "Album artist ID mismatch"
    assert album.artist.name == TEST_ARTIST_NAME, "Album artist name mismatch"
    assert album.tracks is not None, "Album should have tracks"
    assert len(album.tracks) > 0 if album.tracks else False, (
        "Album should have at least one track"
    )

    # Validate album art URL is available
    assert album.art_url is not None, "Album should have art URL"
    logger.debug(f"Album art URL: {album.art_url}")

    # Validate album contains expected number of tracks (6 for Rapture)
    expected_min_tracks = 6
    assert len(album.tracks) >= expected_min_tracks, (
        f"Album '{TEST_ALBUM_NAME}' should contain at least {expected_min_tracks} tracks, got {len(album.tracks) if album.tracks else 0}"
    )

    logger.info(f"Album details: {album.title}")
    logger.info(f"Artist: {album.artist.name}")
    logger.info(f"Total tracks: {len(album.tracks) if album.tracks else 0}")

    # Find our test song in album
    if album.tracks:
        test_track = next(
            (t for t in album.tracks if TEST_TRACK_NAME.lower() in t.title.lower()),
            None,
        )
        assert test_track is not None, (
            f"Test song '{TEST_TRACK_NAME}' not found in album tracks"
        )
        logger.info(f"Found test song: {test_track.title}")


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_bc_album_model(bc_api_client):
    """Test BCAlbum model structure with real data."""
    album = await bc_api_client.get_album(TEST_ARTIST_ID, TEST_ALBUM_ID)

    # Test basic album structure
    assert isinstance(album, BCAlbum), f"Expected BCAlbum, got {type(album)}"
    assert album.id == TEST_ALBUM_ID, "Album ID mismatch"
    assert album.title == TEST_ALBUM_NAME, "Album title mismatch"

    # Test artist relationship
    assert isinstance(album.artist, BCArtist), (
        f"Expected BCArtist, got {type(album.artist)}"
    )
    assert album.artist.id == TEST_ARTIST_ID, "Artist ID mismatch"
    assert album.artist.name == TEST_ARTIST_NAME, "Artist name mismatch"

    # Test URL fields
    assert album.url is not None, "Album URL should not be None"
    assert album.art_url is not None, "Album art URL should not be None"
    assert album.url.startswith("https://"), "Album URL should be HTTPS"
    assert album.art_url.startswith("https://"), "Album art URL should be HTTPS"

    # Test pricing structure
    if album.price is not None:
        assert isinstance(album.price, dict), "Price should be a dictionary"
        assert "currency" in album.price, "Price should have currency"
        assert "amount" in album.price, "Price should have amount"
        assert isinstance(album.price["amount"], (int, float)), (
            "Price amount should be numeric"
        )
        assert isinstance(album.price["currency"], str), (
            "Price currency should be string"
        )

    # Test boolean flags
    assert isinstance(album.is_free, bool), "is_free should be boolean"
    assert isinstance(album.is_preorder, bool), "is_preorder should be boolean"
    assert isinstance(album.is_purchasable, bool), "is_purchasable should be boolean"
    assert isinstance(album.is_set_price, bool), "is_set_price should be boolean"

    # Test metadata fields
    assert isinstance(album.total_tracks, int), "total_tracks should be integer"
    assert album.total_tracks >= 0, "total_tracks should be non-negative"

    # Test optional metadata fields
    if album.about is not None:
        assert isinstance(album.about, str), "about should be string"
    if album.credits is not None:
        assert isinstance(album.credits, str), "credits should be string"
    if album.tags is not None:
        assert isinstance(album.tags, list), "tags should be list"
        assert all(isinstance(tag, str) for tag in album.tags), (
            "tags should contain strings"
        )
    if album.release_date is not None:
        assert isinstance(album.release_date, int), "release_date should be integer"
        assert album.release_date > 0, "release_date should be positive"

    # Test tracks structure
    if album.tracks is not None:
        assert isinstance(album.tracks, list), "tracks should be list"
        assert len(album.tracks) > 0, "tracks list should not be empty"

        # Test each track structure
        for track in album.tracks:
            assert isinstance(track, BCTrack), f"Expected BCTrack, got {type(track)}"
            assert track.id > 0, "Track ID should be positive"
            assert isinstance(track.title, str), "Track title should be string"
            assert len(track.title) > 0, "Track title should not be empty"
            assert isinstance(track.artist, BCArtist), "Track should have artist"
            assert track.artist.id == album.artist.id, (
                "Track artist should match album artist"
            )

            # Test track optional fields
            if track.duration is not None:
                assert isinstance(track.duration, (int, float)), (
                    "Track duration should be numeric"
                )
                assert track.duration > 0, "Track duration should be positive"
            if track.track_number > 0:
                assert isinstance(track.track_number, int), (
                    "Track number should be integer"
                )
            if track.lyrics is not None:
                assert isinstance(track.lyrics, str), "Lyrics should be string"

    # Test album type
    assert isinstance(album.type, str), "type should be string"
    assert album.type in ["album", "album-single", "track"], "Invalid album type"

    logger.info(f"BCAlbum model structure validation passed for: {album.title}")
    logger.debug(f"   - Artist: {album.artist.name}")
    logger.debug(f"   - Tracks: {len(album.tracks) if album.tracks else 0}")
    logger.debug(f"   - Price: {album.price}")
    logger.debug(f"   - Type: {album.type}")
    logger.debug(f"   - Release date: {album.release_date}")
    logger.debug(f"   - Tags: {album.tags}")


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_bc_track_model_structure(bc_api_client):
    """Test BCTrack model structure with real data."""
    album = await bc_api_client.get_album(TEST_ARTIST_ID, TEST_ALBUM_ID)

    assert album.tracks is not None, "Album should have tracks for this test"
    assert len(album.tracks) > 0, "Album should have at least one track"

    # Test the first track (should be our test track)
    first_track = album.tracks[0]
    assert isinstance(first_track, BCTrack), (
        f"Expected BCTrack, got {type(first_track)}"
    )

    # Test basic track structure
    assert first_track.id > 0, "Track ID should be positive"
    assert isinstance(first_track.title, str), "Track title should be string"
    assert len(first_track.title) > 0, "Track title should not be empty"

    # Test artist relationship
    assert isinstance(first_track.artist, BCArtist), (
        f"Expected BCArtist, got {type(first_track.artist)}"
    )
    assert first_track.artist.id == album.artist.id, (
        "Track artist should match album artist"
    )
    assert first_track.artist.name == album.artist.name, (
        "Track artist name should match album artist name"
    )

    # Test album relationship
    assert first_track.album is not None, "Track should have album reference"
    assert first_track.album.id == album.id, "Track album ID should match album ID"
    assert first_track.album.title == album.title, (
        "Track album title should match album title"
    )

    # Test URL field
    if first_track.url is not None:
        assert isinstance(first_track.url, str), "Track URL should be string"
        assert first_track.url.startswith("https://"), "Track URL should be HTTPS"

    # Test duration (can be int or float as we discovered)
    if first_track.duration is not None:
        assert isinstance(first_track.duration, (int, float)), (
            "Duration should be numeric"
        )
        assert first_track.duration > 0, "Duration should be positive"
        logger.debug(
            f"Track duration: {first_track.duration} seconds ({first_track.duration / 60:.2f} minutes)"
        )

    # Test track number
    if first_track.track_number > 0:
        assert isinstance(first_track.track_number, int), (
            "Track number should be integer"
        )
        assert first_track.track_number > 0, "Track number should be positive"

    # Test streaming URL
    if first_track.streaming_url is not None:
        assert isinstance(first_track.streaming_url, dict), (
            "Streaming URL should be dictionary"
        )
        assert len(first_track.streaming_url) > 0, "Streaming URL should not be empty"
        # Check that URLs are valid
        for format_name, url in first_track.streaming_url.items():
            assert isinstance(format_name, str), (
                "Streaming format name should be string"
            )
            assert isinstance(url, str), "Streaming URL should be string"
            assert url.startswith("https://"), "Streaming URL should be HTTPS"
            logger.debug(f"Streaming format: {format_name} -> {url}")

    # Test optional metadata fields
    if first_track.lyrics is not None:
        assert isinstance(first_track.lyrics, str), "Lyrics should be string"
        logger.debug(f"Track has lyrics: {len(first_track.lyrics)} characters")
    else:
        logger.debug("Track has no lyrics")

    if first_track.about is not None:
        assert isinstance(first_track.about, str), "About should be string"
        logger.debug(f"Track about: {first_track.about[:100]}...")

    if first_track.credits is not None:
        assert isinstance(first_track.credits, str), "Credits should be string"
        logger.debug(f"Track credits: {first_track.credits[:100]}...")

    # Test track type
    assert isinstance(first_track.type, str), "Type should be string"
    assert first_track.type == "track", "Track type should be 'track'"

    # Find and test our specific test track
    test_track = None
    if album.tracks:
        test_track = next(
            (t for t in album.tracks if TEST_TRACK_NAME.lower() in t.title.lower()),
            None,
        )

    if test_track:
        logger.info(f"Found and validated test track: {test_track.title}")
        logger.debug(f"   - ID: {test_track.id}")
        logger.debug(f"   - Duration: {test_track.duration} seconds")
        logger.debug(f"   - Track #: {test_track.track_number}")
        logger.debug(f"   - Artist: {test_track.artist.name}")
        logger.debug(
            f"   - Album: {test_track.album.title if test_track.album else 'None'}"
        )
        logger.debug(f"   - Has lyrics: {'Yes' if test_track.lyrics else 'No'}")
        logger.debug(
            f"   - Has streaming URL: {'Yes' if test_track.streaming_url else 'No'}"
        )
    else:
        logger.info(
            f"Test track '{TEST_TRACK_NAME}' not found in album, but other tracks validated successfully"
        )

    logger.info("BCTrack model structure validation passed!")


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_get_track_details(bc_api_client):
    """Test getting detailed track information."""
    track = await bc_api_client.get_track(TEST_ARTIST_ID, TEST_TRACK_ID)

    assert isinstance(track, BCTrack), f"Expected BCTrack, got {type(track)}"
    assert track.id == TEST_TRACK_ID, "Track ID mismatch"
    assert track.title == TEST_TRACK_NAME, "Track title mismatch"
    assert track.artist.id == TEST_ARTIST_ID, "Track artist ID mismatch"
    assert track.artist.name == TEST_ARTIST_NAME, "Track artist name mismatch"

    logger.info(f"Track details: {track.title}")
    logger.info(f"Artist: {track.artist.name}")
    logger.debug(
        f"Duration: {track.duration}s" if track.duration else "Duration: Unknown"
    )
    logger.debug(f"Has lyrics: {'Yes' if track.lyrics else 'No'}")


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_get_artist_discography(bc_api_client):
    """Test getting artist discography."""
    discography = await bc_api_client.get_artist_discography(TEST_ARTIST_ID)

    assert isinstance(discography, list), "Discography should be a list"
    assert len(discography) > 0, "Discography should not be empty"

    logger.info(f"Found {len(discography)} items in discography")

    # Find our test album in discography
    test_album = next(
        (
            item
            for item in discography
            if item.get("item_id") == TEST_ALBUM_ID
            and item.get('title') == TEST_ALBUM_NAME
        ),
        None,
    )
    assert test_album is not None, (
        f"Test album '{TEST_ALBUM_NAME}' not found in discography"
    )
    logger.info(
        f"Found test album in discography: {test_album.get('title', 'Unknown')}"
    )


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_invalid_artist_id(bc_api_client):
    """Test error handling for invalid artist ID."""
    with pytest.raises(BandcampAPIError):
        await bc_api_client.get_artist(999999999)


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_invalid_album_id(bc_api_client):
    """Test error handling for invalid album ID."""
    with pytest.raises(BandcampNotFoundError):
        await bc_api_client.get_album(TEST_ARTIST_ID, 999999999)


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_invalid_track_id(bc_api_client):
    """Test error handling for invalid track ID."""
    with pytest.raises(BandcampNotFoundError):
        await bc_api_client.get_track(TEST_ARTIST_ID, 999999999)
