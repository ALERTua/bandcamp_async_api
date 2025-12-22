"""Shared test fixtures and configuration."""

import os
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from bandcamp_async_api.client import BandcampAPIClient
from dotenv import load_dotenv


pytest_plugins = ('pytest_asyncio',)

load_dotenv()


@pytest_asyncio.fixture(loop_scope="session", name="bc_api_client")
async def _bc_api_client():
    """Fixture to provide an API client."""
    async with BandcampAPIClient(
        identity_token=os.getenv("BANDCAMP_IDENTITY_TOKEN", None)
    ) as bc:
        yield bc


@pytest_asyncio.fixture
async def mock_session():
    """Mock aiohttp ClientSession for testing."""
    session = AsyncMock()
    session.close = AsyncMock()

    # Set up context managers that can be configured by tests
    get_context = AsyncMock()
    get_context.__aenter__ = AsyncMock()
    get_context.__aexit__ = AsyncMock(return_value=None)

    post_context = AsyncMock()
    post_context.__aenter__ = AsyncMock()
    post_context.__aexit__ = AsyncMock(return_value=None)

    # Make session.get and session.post return the context managers directly (not as AsyncMock return values)
    session.get = Mock(return_value=get_context)
    session.post = Mock(return_value=post_context)

    return session


@pytest.fixture
def mock_response():
    """Mock aiohttp ClientResponse."""
    response = Mock()
    response.raise_for_status = Mock()
    response.json = AsyncMock()
    return response


@pytest.fixture
async def mock_async_context():
    """Create a mock async context manager."""

    class MockAsyncContext:
        def __init__(self, response):
            self.response = response

        async def __aenter__(self):
            return self.response

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockAsyncContext


@pytest.fixture
def sample_search_data():
    """Sample search API response data."""
    return {
        "results": [
            {
                "type": "b",
                "id": 123,
                "name": "Test Artist",
                "url": "https://testartist.bandcamp.comhttps://testartist.bandcamp.com",
                "location": "Test City",
                "is_label": False,
                "tag_names": ["electronic", "ambient"],
                "img_id": 456,
                "genre_name": "Electronic",
            },
            {
                "type": "a",
                "id": 789,
                "name": "Test Album",
                "url": "https://testartist.bandcamp.comhttps://testartist.bandcamp.com/album/test-album",
                "band_id": 123,
                "band_name": "Test Artist",
                "art_id": 101112,
            },
            {
                "type": "t",
                "id": 131415,
                "name": "Test Track",
                "url": "https://testartist.bandcamp.comhttps://testartist.bandcamp.com/track/test-track",
                "band_id": 123,
                "band_name": "Test Artist",
                "album_name": "Test Album",
                "album_id": 789,
                "art_id": 101112,
            },
        ]
    }


@pytest.fixture
def sample_artist_data():
    """Sample artist API response data."""
    return {
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


@pytest.fixture
def sample_album_data():
    """Sample album API response data."""
    return {
        "id": 789,
        "title": "Test Album",
        "bandcamp_url": "https://testartist.bandcamp.com/album/test-album",
        "art_id": 101112,
        "release_date": 1640995200,  # 2022-01-01
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


@pytest.fixture
def sample_track_data():
    """Sample track API response data."""
    return {
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


@pytest.fixture
def sample_collection_summary_data():
    """Sample collection summary API response data."""
    return {"fan_id": 999, "collection_count": 5, "wishlist_count": 2}


@pytest.fixture
def sample_collection_items_data():
    """Sample collection items API response data."""
    return {
        "items": [
            {
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
        ],
        "has_more": False,
        "last_token": "token123",
    }
