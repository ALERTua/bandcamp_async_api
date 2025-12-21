"""End-to-end tests for Gaggiuino API."""

import os
import pytest
import pytest_asyncio

from bandcamp_async_api.client import BandcampAPIClient

pytest_plugins = ('pytest_asyncio',)


@pytest_asyncio.fixture(loop_scope="session", name="bc_api_client")
async def _bc_api_client():
    """Fixture to provide an API client."""
    async with BandcampAPIClient(identity_token=os.getenv("BANDCAMP_IDENTITY_TOKEN", None)) as bc:
        yield bc


@pytest.mark.asyncio(loop_scope="session")
async def test_api_client_created(bc_api_client):
    """Test basic API connection."""
    assert bc_api_client is not None
