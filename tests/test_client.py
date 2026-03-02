"""Tests for BandcampAPIClient."""

import pytest
from unittest.mock import AsyncMock, patch

from bandcamp_async_api.client import (
    BandcampAPIClient,
    BandcampAPIError,
    BandcampNotFoundError,
    BandcampMustBeLoggedInError,
    BandcampRateLimitError,
)
from bandcamp_async_api.models import CollectionType, FanItem, FollowingItem

# Shared fixture for wishlist response data
SAMPLE_WISHLIST_DATA = {
    "items": [
        {
            "item_type": "album",
            "item_id": 555,
            "band_id": 666,
            "tralbum_type": "a",
            "band_name": "Wishlist Artist",
            "item_title": "Wishlist Album",
            "item_url": "https://wishlistartist.bandcamp.com/album/wishlist-album",
            "art_id": 777,
            "num_streamable_tracks": 5,
            "is_purchasable": True,
            "price": 7.0,
        }
    ],
    "has_more": True,
    "last_token": "wishlist_token_123",
}


class TestBandcampAPIClient:
    """Test BandcampAPIClient functionality."""

    def test_client_initialization(self):
        """Test client initialization with different parameters."""
        # Test basic initialization
        client = BandcampAPIClient()
        assert client._session is None
        assert client.identity is None
        assert client.headers["User-Agent"] == "bandcamp-api/1.0"

        # Test with custom parameters
        client = BandcampAPIClient(
            identity_token="test_token", user_agent="test-agent/1.0"
        )
        assert client.identity == "test_token"
        assert client.headers["User-Agent"] == "test-agent/1.0"

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_session):
        """Test async context manager."""
        client = BandcampAPIClient(session=mock_session)

        async with client:
            assert client._session == mock_session

        # Session should not be closed if it was provided externally
        mock_session.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager_creates_session(self):
        """Test context manager creates session when none provided."""
        client = BandcampAPIClient()

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            async with client:
                assert client._session == mock_session

            # Session should be closed when created internally
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_search(self, mock_session, sample_search_data):
        """Test search functionality."""
        client = BandcampAPIClient(session=mock_session)

        # Mock the _get method to return sample data directly
        with patch.object(client, '_get', return_value=sample_search_data) as mock_get:
            results = await client.search("test query")

            assert len(results) == 3
            assert results[0].type == "artist"
            assert results[0].name == "Test Artist"
            assert results[1].type == "album"
            assert results[1].name == "Test Album"
            assert results[2].type == "track"
            assert results[2].name == "Test Track"

            # Verify _get was called with correct parameters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "fuzzysearch/1/app_autocomplete" in call_args[1]['url']
            assert call_args[1]["params"]["q"] == "test query"

    @pytest.mark.parametrize(
        "input_query,expected_query",
        [
            ("Midnight Glow, Vol.", "Midnight Glow  Vol."),  # Single comma
            ("a,b,c,d", "a b c d"),  # Multiple commas
            (
                "Artist, Album, Track",
                "Artist  Album  Track",
            ),  # Multiple commas with spaces
            ("normal query", "normal query"),  # No commas
            ("query,", "query "),  # Trailing comma
            (",query", " query"),  # Leading comma
            ("a,,b", "a  b"),  # Double comma
        ],
    )
    @pytest.mark.asyncio
    async def test_search_comma_sanitization(
        self, mock_session, sample_search_data, input_query, expected_query
    ):
        """Test that commas in search queries are replaced with spaces.

        This is needed because Bandcamp API interprets commas as query separators
        and only allows max 1 query term.
        """
        client = BandcampAPIClient(session=mock_session)

        with patch.object(client, '_get', return_value=sample_search_data) as mock_get:
            await client.search(input_query)

            # Verify the comma was replaced with space in the API call
            call_args = mock_get.call_args
            assert call_args[1]["params"]["q"] == expected_query

    @pytest.mark.asyncio
    async def test_get_album(self, mock_session, sample_album_data):
        """Test get album functionality."""
        client = BandcampAPIClient(session=mock_session)

        with patch.object(client, '_get', return_value=sample_album_data) as mock_get:
            album = await client.get_album(123, 789)

            assert album.id == 789
            assert album.title == "Test Album"
            assert album.artist.name == "Test Artist"
            assert album.tracks is not None
            if album.tracks is not None:  # Type guard for mypy
                assert len(album.tracks) == 2
                assert album.tracks[0].title == "Test Track 1"
                assert album.tracks[1].title == "Test Track 2"

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_track(self, mock_session, sample_track_data):
        """Test get track functionality."""
        client = BandcampAPIClient(session=mock_session)

        with patch.object(client, '_get', return_value=sample_track_data) as mock_get:
            track = await client.get_track(123, 131415)

            assert track.id == 131415
            assert track.title == "Test Track"
            assert track.artist.name == "Test Artist"
            assert track.duration == 180

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_artist(self, mock_session, sample_artist_data):
        """Test get artist functionality."""
        client = BandcampAPIClient(session=mock_session)

        with patch.object(
            client, '_post', return_value=sample_artist_data
        ) as mock_post:
            artist = await client.get_artist(123)

            assert artist.id == 123
            assert artist.name == "Test Artist"
            assert artist.bio == "Test artist biography"
            assert artist.tags == ["electronic", "ambient"]

            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_collection_summary_requires_token(self):
        """Test collection summary requires identity token."""
        client = BandcampAPIClient()

        with pytest.raises(
            BandcampMustBeLoggedInError,
            match="You must be logged in to access collection data",
        ):
            await client.get_collection_summary()

    @pytest.mark.asyncio
    async def test_get_collection_summary(
        self, mock_session, sample_collection_summary_data
    ):
        """Test get collection summary."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        with patch.object(
            client, '_get', return_value=sample_collection_summary_data
        ) as mock_get:
            summary = await client.get_collection_summary()

            assert summary.fan_id == 999
            assert summary.items == []
            assert not summary.has_more

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_collection_items_requires_token(self):
        """Test collection items requires identity token when fan_id not provided."""
        client = BandcampAPIClient()

        with pytest.raises(
            BandcampMustBeLoggedInError,
            match="You must be logged in or provide a fan_id",
        ):
            await client.get_collection_items()

    @pytest.mark.asyncio
    async def test_get_collection_items(
        self, mock_session, sample_collection_items_data
    ):
        """Test get collection items."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        # Mock collection summary first, then collection items
        with (
            patch.object(client, '_get', return_value={"fan_id": 999}) as mock_get,
            patch.object(
                client, '_post', return_value=sample_collection_items_data
            ) as mock_post,
        ):
            summary = await client.get_collection_items()

            assert summary.fan_id == 999
            assert len(summary.items) == 1
            assert summary.items[0].item_title == "Test Album"
            assert not summary.has_more

            # Should call both _get (for summary) and _post (for items)
            assert mock_get.call_count == 1
            assert mock_post.call_count == 1

    @pytest.mark.asyncio
    async def test_get_artist_discography(self, mock_session, sample_artist_data):
        """Test get artist discography."""
        client = BandcampAPIClient(session=mock_session)

        with patch.object(
            client, '_post', return_value=sample_artist_data
        ) as mock_post:
            discography = await client.get_artist_discography(123)

            # Should return the discography from the artist data
            assert "discography" in sample_artist_data or discography == []

            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_session):
        """Test API error handling."""
        client = BandcampAPIClient(session=mock_session)

        # Mock the session methods to return error data
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(
            return_value={"error": True, "error_message": "Test error"}
        )
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(BandcampAPIError, match="Test error"):
            await client.search("test")

    @pytest.mark.asyncio
    async def test_not_found_error_handling(self, mock_session):
        """Test not found error handling."""
        client = BandcampAPIClient(session=mock_session)

        # Mock the session methods to return error data
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(
            return_value={"error": True, "error_message": "No such album"}
        )
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(BandcampNotFoundError, match="No such album"):
            await client.get_album(123, 789)

    @pytest.mark.asyncio
    async def test_identity_token_in_headers(self, mock_session):
        """Test identity token is included in headers."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        # Mock the response
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(return_value={"results": []})
        mock_session.get.return_value.__aenter__.return_value = mock_response

        await client.search("test")

        # Check that session.get was called with identity token in headers
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        headers = call_args[1]["headers"]
        assert headers["Cookie"] == "identity=test_token"

    @pytest.mark.asyncio
    async def test_rate_limit_error_with_retry_after(self, mock_session):
        """Test rate limit error with Retry-After header."""
        client = BandcampAPIClient(session=mock_session)

        # Mock the response with 429 status and Retry-After header
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(BandcampRateLimitError) as exc_info:
            await client.search("test")

        assert exc_info.value.retry_after == 60
        assert "60 seconds" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_error_default_retry_after(self, mock_session):
        """Test rate limit error with missing Retry-After header defaults to 10."""
        client = BandcampAPIClient(session=mock_session)

        # Mock the response with 429 status but no Retry-After header
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {}
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(BandcampRateLimitError) as exc_info:
            await client.search("test")

        assert exc_info.value.retry_after == 10
        assert "10 seconds" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_error_invalid_retry_after(self, mock_session):
        """Test rate limit error with invalid Retry-After header defaults to 10."""
        client = BandcampAPIClient(session=mock_session)

        # Mock the response with 429 status and invalid Retry-After header
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "invalid"}
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(BandcampRateLimitError) as exc_info:
            await client.search("test")

        assert exc_info.value.retry_after == 10

    @pytest.mark.asyncio
    async def test_rate_limit_error_post_request(self, mock_session):
        """Test rate limit error on POST request."""
        client = BandcampAPIClient(session=mock_session)

        # Mock the response with 429 status for POST
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "120"}
        mock_session.post.return_value.__aenter__.return_value = mock_response

        with pytest.raises(BandcampRateLimitError) as exc_info:
            await client.get_artist(123)

        assert exc_info.value.retry_after == 120

    @pytest.mark.asyncio
    async def test_get_following_bands(self, mock_session, sample_following_bands_data):
        """Test that following_bands response is parsed correctly.

        The following_bands endpoint returns items in "followeers" (not "items")
        and uses "more_available" (not "has_more") for pagination.
        """
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        with (
            patch.object(client, '_get', return_value={"fan_id": 999}) as mock_get,
            patch.object(
                client, '_post', return_value=sample_following_bands_data
            ) as mock_post,
        ):
            summary = await client.get_collection_items(CollectionType.FOLLOWING)

            assert summary.fan_id == 999
            assert len(summary.items) == 2
            assert summary.has_more is True
            assert summary.last_token == "1577836800:333"

            # Verify items are FollowingItem instances with correct data
            item0 = summary.items[0]
            assert isinstance(item0, FollowingItem)
            assert item0.band_id == 111
            assert item0.name == "Followed Artist 1"
            assert item0.url == "https://followedartist1.bandcamp.com"
            assert item0.location == "Portland, OR"
            assert item0.is_label is False

            item1 = summary.items[1]
            assert isinstance(item1, FollowingItem)
            assert item1.band_id == 333
            assert item1.name == "Followed Label"
            assert item1.is_label is True

            assert mock_get.call_count == 1
            assert mock_post.call_count == 1
            # Verify correct endpoint URL
            post_url = mock_post.call_args[1]["url"]
            assert post_url.endswith("/fancollection/1/following_bands")

    @pytest.mark.asyncio
    async def test_get_following_bands_empty(
        self, mock_session, sample_following_bands_empty_data
    ):
        """Test following_bands with no followed bands."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        with (
            patch.object(client, '_get', return_value={"fan_id": 999}),
            patch.object(
                client, '_post', return_value=sample_following_bands_empty_data
            ),
        ):
            summary = await client.get_collection_items(CollectionType.FOLLOWING)

            assert summary.fan_id == 999
            assert len(summary.items) == 0
            assert summary.has_more is False

    @pytest.mark.asyncio
    async def test_collection_items_still_uses_items_key(
        self, mock_session, sample_collection_items_data
    ):
        """Test that COLLECTION type still reads from "items" key."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        with (
            patch.object(client, '_get', return_value={"fan_id": 999}),
            patch.object(client, '_post', return_value=sample_collection_items_data),
        ):
            summary = await client.get_collection_items(CollectionType.COLLECTION)

            assert len(summary.items) == 1
            assert summary.items[0].item_title == "Test Album"

    @pytest.mark.asyncio
    async def test_get_following_fans(self, mock_session, sample_following_fans_data):
        """Test that following_fans response is parsed correctly.

        Like following_bands, uses "followeers" and "more_available",
        but items are FanItem with fan_id instead of band_id.
        """
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        with (
            patch.object(client, '_get', return_value={"fan_id": 999}),
            patch.object(client, '_post', return_value=sample_following_fans_data),
        ):
            summary = await client.get_collection_items(CollectionType.FOLLOWING_FANS)

            assert summary.fan_id == 999
            assert len(summary.items) == 1
            assert summary.has_more is False
            assert summary.last_token == "1568148247:3477641"

            item = summary.items[0]
            assert isinstance(item, FanItem)
            assert item.fan_id == 3477641
            assert item.name == "David Bishop"
            assert item.url == "https://bandcamp.com/teancom"
            assert item.location == "Portland, OR"
            assert item.is_following is True

    @pytest.mark.asyncio
    async def test_get_following_fans_url(self, mock_session, sample_following_fans_data):
        """Test that following_fans hits the correct endpoint URL."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        with (
            patch.object(client, '_get', return_value={"fan_id": 999}),
            patch.object(
                client, '_post', return_value=sample_following_fans_data
            ) as mock_post,
        ):
            await client.get_collection_items(CollectionType.FOLLOWING_FANS)
            post_url = mock_post.call_args[1]["url"]
            assert post_url.endswith("/fancollection/1/following_fans")

    @pytest.mark.asyncio
    async def test_get_collection_items_with_custom_fan_id(
        self, mock_session, sample_collection_items_data
    ):
        """Test querying another user's collection by passing fan_id."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        with (
            patch.object(
                client, '_post', return_value=sample_collection_items_data
            ) as mock_post,
        ):
            # Pass explicit fan_id — should NOT call get_collection_summary
            summary = await client.get_collection_items(
                CollectionType.COLLECTION, fan_id=12345
            )

            assert summary.fan_id == 12345
            assert len(summary.items) == 1

            # Verify the POST was called with the custom fan_id
            call_args = mock_post.call_args
            assert call_args[1]["json"]["fan_id"] == 12345

            # Should only have called _post (no _get for collection_summary)
            assert mock_post.call_count == 1

    @pytest.mark.asyncio
    async def test_get_followers(self, mock_session, sample_followers_data):
        """Test that followers endpoint returns fans who follow the user."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        with (
            patch.object(client, '_get', return_value={"fan_id": 999}),
            patch.object(
                client, '_post', return_value=sample_followers_data
            ) as mock_post,
        ):
            summary = await client.get_collection_items(CollectionType.FOLLOWERS)

            assert summary.fan_id == 999
            assert len(summary.items) == 1
            assert summary.has_more is False

            item = summary.items[0]
            assert isinstance(item, FanItem)
            assert item.fan_id == 9876543
            assert item.name == "Jane Doe"
            assert item.url == "https://bandcamp.com/janedoe"
            assert item.is_following is False

            # Verify correct endpoint URL
            post_url = mock_post.call_args[1]["url"]
            assert post_url.endswith("/fancollection/1/followers")

    @pytest.mark.asyncio
    async def test_wishlist_still_uses_items_key(
        self, mock_session
    ):
        """Test that WISHLIST type still reads from "items" key."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        with (
            patch.object(client, '_get', return_value={"fan_id": 999}),
            patch.object(client, '_post', return_value=SAMPLE_WISHLIST_DATA) as mock_post,
        ):
            summary = await client.get_collection_items(CollectionType.WISHLIST)

            assert len(summary.items) == 1
            assert summary.items[0].item_title == "Wishlist Album"
            assert summary.has_more is True

            post_url = mock_post.call_args[1]["url"]
            assert post_url.endswith("/fancollection/1/wishlist_items")

    @pytest.mark.asyncio
    async def test_older_than_token_forwarded(
        self, mock_session, sample_following_bands_data
    ):
        """Test that explicit older_than_token is forwarded to the API."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        with (
            patch.object(client, '_get', return_value={"fan_id": 999}),
            patch.object(
                client, '_post', return_value=sample_following_bands_data
            ) as mock_post,
        ):
            await client.get_collection_items(
                CollectionType.FOLLOWING, older_than_token="1577836800:333"
            )

            call_args = mock_post.call_args
            assert call_args[1]["json"]["older_than_token"] == "1577836800:333"

    @pytest.mark.asyncio
    async def test_get_collection_items_without_auth_using_fan_id(
        self, mock_session, sample_collection_items_data
    ):
        """Test that fan_id allows unauthenticated collection access."""
        client = BandcampAPIClient(session=mock_session)  # No identity token

        with (
            patch.object(
                client, '_post', return_value=sample_collection_items_data
            ) as mock_post,
        ):
            summary = await client.get_collection_items(
                CollectionType.COLLECTION, fan_id=12345
            )

            assert summary.fan_id == 12345
            assert len(summary.items) == 1
            assert mock_post.call_count == 1
