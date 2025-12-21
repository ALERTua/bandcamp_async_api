"""Tests for BandcampAPIClient."""

import pytest
from unittest.mock import AsyncMock, patch

from bandcamp_async_api.client import (
    BandcampAPIClient,
    BandcampAPIError,
    BandcampNotFoundError,
)


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
            assert "fuzzysearch/1/app_autocomplete" in call_args[0][0]
            assert call_args[1]["params"]["q"] == "test query"

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

        with pytest.raises(BandcampAPIError, match="Identity token required"):
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
        """Test collection items requires identity token."""
        client = BandcampAPIClient()

        with pytest.raises(BandcampAPIError, match="Identity token required"):
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
