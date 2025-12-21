"""Integration tests for bandcamp_async_api."""

import pytest
from unittest.mock import AsyncMock, patch

from bandcamp_async_api.client import BandcampAPIClient


class TestBandcampAPIIntegration:
    """Integration tests for end-to-end functionality."""

    @pytest.mark.asyncio
    async def test_full_search_and_get_album_workflow(self, mock_session, sample_search_data, sample_album_data):
        """Test complete workflow: search -> get album."""
        client = BandcampAPIClient(session=mock_session)

        # Mock the methods to return sample data
        with patch.object(client, '_get', side_effect=[sample_search_data, sample_album_data]) as mock_get:
            # Execute workflow
            search_results = await client.search("test artist")
            album = await client.get_album(
                search_results[1].artist_id,
                search_results[1].id
            )

            # Verify search results
            assert len(search_results) == 3
            album_result = search_results[1]  # Second result should be the album
            assert album_result.type == "album"
            assert album_result.name == "Test Album"

            # Verify album data
            assert album.id == search_results[1].id
            assert album.title == "Test Album"
            assert album.artist.name == "Test Artist"
            assert album.tracks is not None
            assert len(album.tracks) == 2

            # Verify API calls were made correctly
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_artist_discography_workflow(self, mock_session, sample_artist_data):
        """Test artist discography workflow."""
        client = BandcampAPIClient(session=mock_session)

        with patch.object(client, '_post', return_value=sample_artist_data) as mock_post:
            # Execute workflow
            artist = await client.get_artist(123)
            await client.get_artist_discography(123)

            # Verify artist data
            assert artist.id == 123
            assert artist.name == "Test Artist"

            # Verify discography call was made
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_collection_workflow(self, mock_session, sample_collection_summary_data, sample_collection_items_data):
        """Test collection access workflow."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token")

        with patch.object(client, '_get', return_value=sample_collection_summary_data), \
             patch.object(client, '_post', return_value=sample_collection_items_data):

            # Execute workflow
            summary = await client.get_collection_summary()
            collection_items = await client.get_collection_items()

            # Verify collection summary
            assert summary.fan_id == 999
            assert summary.items == []

            # Verify collection items
            assert collection_items.fan_id == 999
            assert len(collection_items.items) == 1
            assert collection_items.items[0].item_title == "Test Album"

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, mock_session):
        """Test error handling across multiple operations."""
        client = BandcampAPIClient(session=mock_session)

        # Mock error response that bypasses _get method
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(return_value={"error": True, "error_message": "API Error"})
        mock_session.get.return_value.__aenter__.return_value = mock_response

        # Test that errors are properly propagated
        with pytest.raises(Exception):  # Could be BandcampAPIError or other
            await client.search("test")

    @pytest.mark.asyncio
    async def test_session_reuse_across_operations(self, mock_session, sample_search_data, sample_artist_data):
        """Test that the same session is reused across multiple operations."""
        client = BandcampAPIClient(session=mock_session)

        with patch.object(client, '_get', return_value=sample_search_data) as mock_get, \
             patch.object(client, '_post', return_value=sample_artist_data) as mock_post:

            # Execute multiple operations
            await client.search("test")
            await client.get_artist(123)

            # Verify the same session was used for both operations
            assert client._session == mock_session

            # Verify both operations made their respective calls
            assert mock_get.call_count == 1
            assert mock_post.call_count == 1

    @pytest.mark.asyncio
    async def test_context_manager_integration(self):
        """Test full context manager integration."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            client = BandcampAPIClient()

            async with client:
                # Session should be created and assigned
                assert client._session == mock_session

            # Session should be closed after context manager exits
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_identity_token_integration(self, mock_session, sample_collection_summary_data):
        """Test identity token handling across operations."""
        client = BandcampAPIClient(session=mock_session, identity_token="test_token_123")

        # Mock the response
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(return_value=sample_collection_summary_data)
        mock_session.get.return_value.__aenter__.return_value = mock_response

        # Execute operation that requires identity
        summary = await client.get_collection_summary()

        # Verify the identity token was included in headers
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        headers = call_args[1]["headers"]
        assert headers["Cookie"] == "identity=test_token_123"

        # Verify operation succeeded
        assert summary.fan_id == 999

    @pytest.mark.asyncio
    async def test_data_consistency_across_operations(self, mock_session, sample_album_data):
        """Test data consistency when parsing related objects."""
        client = BandcampAPIClient(session=mock_session)

        with patch.object(client, '_get', return_value=sample_album_data) as mock_get:
            album = await client.get_album(123, 789)

            # Verify album and track artist consistency
            assert album.artist.id == 123
            assert album.artist.name == "Test Artist"

            # All tracks should have the same artist as the album
            if album.tracks is not None:
                for track in album.tracks:
                    assert track.artist == album.artist
                    assert track.album == album

            mock_get.assert_called_once()
