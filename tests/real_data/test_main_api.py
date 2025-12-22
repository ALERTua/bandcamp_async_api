"""Real data tests for main Bandcamp API methods.

These tests require BANDCAMP_IDENTITY_TOKEN environment variable to be set.
Tests are marked as manual and should be run explicitly with:
    pytest -m manual tests/real_data/

Run with: pytest -m manual tests/real_data/test_main_api.py -v
"""

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
    print(f"Found artist: {pathos_result.name} (ID: {pathos_result.id})")


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
    print(f"Found album: {album_result.name} (ID: {album_result.id})")


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
    print(f"Found track: {track_result.name} (ID: {track_result.id})")

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

    print(f"Artist details: {artist.name}")
    print(f"Location: {artist.location}")
    print(f"Bio: {artist.bio[:100] if artist.bio else 'None'}...")
    print(f"Tags: {artist.tags}")


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
    print(f"Album art URL: {album.art_url}")

    # Validate album contains expected number of tracks (6 for Rapture)
    expected_min_tracks = 6
    assert len(album.tracks) >= expected_min_tracks, (
        f"Album '{TEST_ALBUM_NAME}' should contain at least {expected_min_tracks} tracks, got {len(album.tracks) if album.tracks else 0}"
    )

    print(f"Album details: {album.title}")
    print(f"Artist: {album.artist.name}")
    print(f"Total tracks: {len(album.tracks) if album.tracks else 0}")

    # Find our test song in album
    if album.tracks:
        test_track = next(
            (t for t in album.tracks if TEST_TRACK_NAME.lower() in t.title.lower()),
            None,
        )
        assert test_track is not None, (
            f"Test song '{TEST_TRACK_NAME}' not found in album tracks"
        )
        print(f"Found test song: {test_track.title}")


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

    print(f"Track details: {track.title}")
    print(f"Artist: {track.artist.name}")
    print(f"Duration: {track.duration}s" if track.duration else "Duration: Unknown")
    print(f"Has lyrics: {'Yes' if track.lyrics else 'No'}")


@manual
@pytest.mark.asyncio(loop_scope="session")
async def test_get_artist_discography(bc_api_client):
    """Test getting artist discography."""
    discography = await bc_api_client.get_artist_discography(TEST_ARTIST_ID)

    assert isinstance(discography, list), "Discography should be a list"
    assert len(discography) > 0, "Discography should not be empty"

    print(f"Found {len(discography)} items in discography")

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
    print(f"Found test album in discography: {test_album.get('title', 'Unknown')}")


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
