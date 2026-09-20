"""Regression tests for unexpected Bandcamp API responses."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from bandcamp_async_api import (
    BandcampAPIClient,
    BandcampRateLimitError,
    BandcampUnexpectedResponseError,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content_type", "body"),
    [
        ("text/html", "<html>private challenge details</html>"),
        ("application/json", "not json: private details"),
    ],
)
async def test_unexpected_response(content_type, body):
    """Real aiohttp responses become actionable errors without leaking request data."""

    async def handler(request):
        return web.Response(text=body, content_type=content_type)

    app = web.Application()
    app.router.add_get("/api/fuzzysearch/1/app_autocomplete", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    try:
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = runner.addresses[0][1]
        async with BandcampAPIClient(identity_token="private-cookie") as client:
            client.BASE_URL = f"http://127.0.0.1:{port}/api"
            with pytest.raises(BandcampUnexpectedResponseError) as exc:
                await client.search("private-query")
        text = str(exc.value)
        assert "unexpected or malformed response instead of JSON" in text
        assert "HTTP 200" in text
        assert "Try again later" in text
        assert "private" not in text
        assert exc.value.__cause__ is not None
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_rate_limit_remains_distinct():
    """Rate limits retain their existing retry guidance and are not decoded."""
    response = MagicMock(status=429, headers={"Retry-After": "3"})
    response.json = AsyncMock()
    session = MagicMock()
    session.get.return_value.__aenter__ = AsyncMock(return_value=response)
    session.get.return_value.__aexit__ = AsyncMock(return_value=False)
    client = BandcampAPIClient(session=session)
    with pytest.raises(BandcampRateLimitError) as exc:
        await client.search("test")
    assert exc.value.retry_after == 3
    response.json.assert_not_awaited()
