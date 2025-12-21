"""Basic integration tests for bandcamp_async_api."""

import pytest

from bandcamp_async_api.client import BandcampAPIClient


class TestBasicIntegration:
    """Basic integration tests to ensure core functionality works."""

    @pytest.mark.asyncio
    async def test_client_context_manager(self, bc_api_client):
        """Test that client can be used as context manager."""
        # Client fixture already handles context manager
        assert bc_api_client is not None
        assert hasattr(bc_api_client, 'search')
        assert hasattr(bc_api_client, 'get_album')
        assert hasattr(bc_api_client, 'get_artist')

    @pytest.mark.asyncio
    async def test_client_initialization_options(self):
        """Test client initialization with various options."""
        # Test default initialization
        client = BandcampAPIClient()
        assert client.identity is None
        assert client.headers["User-Agent"] == "bandcamp-api/1.0"

        # Test with identity token
        client_with_token = BandcampAPIClient(identity_token="test_token")
        assert client_with_token.identity == "test_token"

        # Test with custom user agent
        client_with_ua = BandcampAPIClient(user_agent="custom-agent/1.0")
        assert client_with_ua.headers["User-Agent"] == "custom-agent/1.0"

    def test_imports(self):
        """Test that all main components can be imported."""
        from bandcamp_async_api.client import BandcampAPIClient
        from bandcamp_async_api.models import BCAlbum, BCArtist, BCTrack
        from bandcamp_async_api.parsers import BandcampParsers

        # Verify classes exist and are importable
        assert BandcampAPIClient
        assert BCAlbum
        assert BCArtist
        assert BCTrack
        assert BandcampParsers

    def test_model_instantiation(self):
        """Test that models can be instantiated with minimal data."""
        from bandcamp_async_api.models import BCArtist, BCAlbum, BCTrack

        artist = BCArtist(id=1, name="Test Artist")
        assert artist.id == 1
        assert artist.name == "Test Artist"

        album = BCAlbum(id=1, title="Test Album", artist=artist)
        assert album.id == 1
        assert album.title == "Test Album"
        assert album.artist == artist

        track = BCTrack(id=1, title="Test Track", artist=artist)
        assert track.id == 1
        assert track.title == "Test Track"
        assert track.artist == artist
