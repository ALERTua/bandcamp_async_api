"""Shared test fixtures and configuration."""

import logging
import os
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from bandcamp_async_api.client import BandcampAPIClient
from dotenv import load_dotenv


pytest_plugins = ('pytest_asyncio',)

load_dotenv()


def pytest_configure(config):
    """Configure logging for pytest."""
    # Set up basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[logging.StreamHandler()],
    )

    # Set specific log levels for different modules
    logging.getLogger("bandcamp_async_api").setLevel(logging.DEBUG)
    logging.getLogger("tests").setLevel(logging.INFO)
    logging.getLogger("tests.real_data").setLevel(logging.INFO)


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


@pytest.fixture
def sample_following_bands_data():
    """Sample following_bands API response data."""
    return {
        "followeers": [
            {
                "band_id": 111,
                "name": "Followed Artist 1",
                "url_hints": {"subdomain": "followedartist1", "custom_domain": None},
                "image_id": 222,
                "location": "Portland, OR",
                "date_followed": "18 Dec 2013 07:53:53 GMT",
                "is_label": False,
                "token": "1387353233:111",
            },
            {
                "band_id": 333,
                "name": "Followed Label",
                "url_hints": {"subdomain": "followedlabel", "custom_domain": None},
                "image_id": 444,
                "location": "Brooklyn, NY",
                "date_followed": "01 Jan 2020 00:00:00 GMT",
                "is_label": True,
                "token": "1577836800:333",
            },
        ],
        "more_available": True,
        "last_token": "1577836800:333",
    }


@pytest.fixture
def sample_following_bands_empty_data():
    """Sample following_bands API response with no followed bands."""
    return {
        "followeers": [],
        "more_available": False,
        "last_token": None,
    }


@pytest.fixture
def sample_following_fans_data():
    """Sample following_fans API response data."""
    return {
        "followeers": [
            {
                "fan_id": 3477641,
                "band_id": None,
                "fan_url": None,
                "image_id": 29851498,
                "trackpipe_url": "https://bandcamp.com/teancom",
                "name": "David Bishop",
                "is_following": True,
                "location": "Portland, OR",
                "date_followed": "10 Sep 2019 20:44:07 GMT",
                "token": "1568148247:3477641",
            },
        ],
        "more_available": False,
        "last_token": "1568148247:3477641",
    }


@pytest.fixture
def sample_followers_data():
    """Sample followers API response data (fans who follow the queried user)."""
    return {
        "followeers": [
            {
                "fan_id": 9876543,
                "band_id": None,
                "fan_url": None,
                "image_id": 11223344,
                "trackpipe_url": "https://bandcamp.com/janedoe",
                "name": "Jane Doe",
                "is_following": False,
                "location": "Seattle, WA",
                "date_followed": "30 Aug 2019 17:00:58 GMT",
                "token": "1567184458:9876543",
            },
        ],
        "more_available": False,
        "last_token": "1567184458:9876543",
    }


@pytest.fixture
def sample_feed_data():
    """Sample fan_dash_feed_updates API response data."""
    return {
        "ok": True,
        "stories": {
            "entries": [
                {
                    "fan_id": 4407009,
                    "item_id": 3105067265,
                    "item_type": "t",
                    "tralbum_id": 3105067265,
                    "tralbum_type": "t",
                    "band_id": 1942662887,
                    "story_date": "13 Mar 2026 18:27:25 GMT",
                    "story_type": "np",
                    "item_title": "Detectorists",
                    "item_url": "https://johnny-flynn.bandcamp.com/track/detectorists",
                    "item_art_url": "https://f4.bcbits.com/img/a3133764461_9.jpg",
                    "item_art_id": 3133764461,
                    "band_name": "Johnny Flynn",
                    "band_url": "https://johnny-flynn.bandcamp.com",
                    "genre_id": 12,
                    "is_purchasable": True,
                    "currency": "GBP",
                    "price": 1.5,
                    "is_preorder": False,
                    "num_streamable_tracks": 1,
                    "also_collected_count": 16,
                    "featured_track": 3105067265,
                    "featured_track_title": "Detectorists",
                    "featured_track_duration": 125.945,
                    "featured_track_encodings_id": 3295429770,
                    "tags": [{"name": "Folk", "norm_name": "folk"}],
                },
                {
                    "fan_id": 999,
                    "item_id": 4182926504,
                    "item_type": "a",
                    "tralbum_id": 4182926504,
                    "tralbum_type": "a",
                    "band_id": 1942662887,
                    "story_date": "06 Mar 2026 15:15:14 GMT",
                    "story_type": "nr",
                    "item_title": "Been Listening",
                    "item_url": "https://johnny-flynn.bandcamp.com/album/been-listening",
                    "item_art_url": "https://f4.bcbits.com/img/a3786075937_9.jpg",
                    "item_art_id": 3786075937,
                    "band_name": "Johnny Flynn",
                    "band_url": "https://johnny-flynn.bandcamp.com",
                    "genre_id": 12,
                    "is_purchasable": True,
                    "currency": "GBP",
                    "price": 9.0,
                    "album_id": 4182926504,
                    "album_title": "Been Listening",
                    "featured_track": 2747948712,
                    "featured_track_title": "The Water",
                    "featured_track_duration": 252.853,
                    "featured_track_number": 7,
                    "featured_track_encodings_id": 2919269361,
                    "num_streamable_tracks": 11,
                    "also_collected_count": 3,
                    "tags": [{"name": "Folk", "norm_name": "folk"}],
                },
            ],
            "oldest_story_date": 1769576630,
            "newest_story_date": 1773426445,
            "track_list": [
                {
                    "track_id": 3105067265,
                    "title": "Detectorists",
                    "track_num": None,
                    "streaming_url": {
                        "mp3-128": "https://bandcamp.com/stream_redirect?track_id=3105067265"
                    },
                    "duration": 125.945,
                    "encodings_id": 3295429770,
                    "album_title": "Detectorists (OST)",
                    "band_name": "Johnny Flynn",
                    "art_id": 3133764461,
                    "album_id": None,
                    "band_id": 1942662887,
                    "is_purchasable": True,
                    "currency": "GBP",
                    "price": 1.5,
                    "track_url": "https://johnny-flynn.bandcamp.com/track/detectorists",
                },
                {
                    "track_id": 2747948712,
                    "title": "The Water",
                    "track_num": 7,
                    "streaming_url": {
                        "mp3-128": "https://bandcamp.com/stream_redirect?track_id=2747948712"
                    },
                    "duration": 252.853,
                    "album_title": "Been Listening",
                    "band_name": "Johnny Flynn",
                    "art_id": 3786075937,
                    "album_id": 4182926504,
                    "band_id": 1942662887,
                    "is_purchasable": True,
                    "currency": "GBP",
                    "price": 9.0,
                    "track_url": "https://johnny-flynn.bandcamp.com/album/been-listening",
                },
            ],
            "query_times": {"stories": 0.05},
            "feed_timestamp": None,
        },
        "fan_info": {
            "4407009": {
                "fan_id": 4407009,
                "name": "Test Fan",
                "username": "testfan",
                "trackpipe_url": "https://bandcamp.com/testfan",
                "image_id": 7864392,
                "collection_size": 4100,
                "fav_genre_name": "Alternative",
            },
        },
        "band_info": {
            "1942662887": {
                "name": "Johnny Flynn",
                "band_id": 1942662887,
                "image_id": 12345,
                "genre_id": 12,
                "followed": 1,
            },
        },
        "story_collectors": {},
        "item_lookup": {},
    }


@pytest.fixture
def sample_feed_empty_data():
    """Sample fan_dash_feed_updates response with no stories."""
    return {
        "ok": True,
        "stories": {
            "entries": [],
            "oldest_story_date": None,
            "newest_story_date": None,
            "track_list": [],
            "query_times": {},
            "feed_timestamp": None,
        },
        "fan_info": {},
        "band_info": {},
        "story_collectors": {},
        "item_lookup": {},
    }
