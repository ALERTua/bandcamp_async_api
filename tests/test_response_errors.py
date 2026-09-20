"""Regression tests for unexpected Bandcamp API responses."""

import logging
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from aiohttp import web

from bandcamp_async_api import (
    BandcampAPIClient,
    BandcampRateLimitError,
    BandcampUnexpectedResponseError,
)

SEARCH_PATH = "/api/fuzzysearch/1/app_autocomplete"


@asynccontextmanager
async def search_server(handler, extra_routes=()):
    """Serve the search endpoint locally and yield a client pointed at it."""
    app = web.Application()
    app.router.add_get(SEARCH_PATH, handler)
    for path, extra_handler in extra_routes:
        app.router.add_get(path, extra_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    try:
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = runner.addresses[0][1]
        async with BandcampAPIClient(identity_token="private-cookie") as client:
            client.BASE_URL = f"http://127.0.0.1:{port}/api"
            yield client
    finally:
        await runner.cleanup()


def body_handler(body, content_type, status=200):
    """Build a handler that answers with a fixed body and records its calls."""

    async def handler(request):
        handler.calls.append(request.path)
        return web.Response(text=body, content_type=content_type, status=status)

    handler.calls = []
    return handler


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content_type", "body"),
    [
        ("text/html", "<html>private challenge details</html>"),
        ("application/json", "not json: private details"),
    ],
)
async def test_unexpected_response(content_type, body):
    """Real aiohttp responses become errors whose own message holds no request data."""
    handler = body_handler(body, content_type)
    async with search_server(handler) as client:
        with pytest.raises(BandcampUnexpectedResponseError) as exc:
            await client.search("private-query")

    assert handler.calls == [SEARCH_PATH]
    text = str(exc.value)
    assert "response that is not usable JSON" in text
    assert "HTTP 200" in text
    assert "Try again later" in text
    assert "private" not in text
    assert exc.value.__cause__ is not None


@pytest.mark.asyncio
async def test_cause_keeps_the_request_url():
    """The chained cause keeps the URL that the message drops, so debugging works."""
    handler = body_handler("<html>x</html>", "text/html")
    async with search_server(handler) as client:
        with pytest.raises(BandcampUnexpectedResponseError) as exc:
            await client.search("private-query")

    assert isinstance(exc.value.__cause__, aiohttp.ContentTypeError)
    assert "private-query" in str(exc.value.__cause__)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expect_retry_hint"),
    [(400, False), (404, False), (499, False), (500, True), (503, True)],
)
async def test_error_page_becomes_a_bandcamp_error(status, expect_retry_hint):
    """An error page becomes a Bandcamp error, and only a server error invites a retry."""
    handler = body_handler("<html>error page</html>", "text/html", status=status)
    async with search_server(handler) as client:
        with pytest.raises(BandcampUnexpectedResponseError) as exc:
            await client.search("private-query")

    assert handler.calls == [SEARCH_PATH]
    text = str(exc.value)
    assert f"HTTP {status}" in text
    assert ("Try again later" in text) is expect_retry_hint
    assert "private" not in text


@pytest.mark.asyncio
@pytest.mark.parametrize("body", ["", "   ", "null", "[1, 2]"])
async def test_json_body_that_is_not_an_object(body):
    """A body that decodes to something other than an object is an unexpected response."""
    handler = body_handler(body, "application/json")
    async with search_server(handler) as client:
        with pytest.raises(BandcampUnexpectedResponseError) as exc:
            await client.search("private-query")

    assert "HTTP 200" in str(exc.value)


@pytest.mark.asyncio
async def test_empty_body_on_an_error_status():
    """An empty body on an error status is reported as an unexpected response."""
    handler = body_handler("", "application/json", status=503)
    async with search_server(handler) as client:
        with pytest.raises(BandcampUnexpectedResponseError) as exc:
            await client.search("private-query")

    text = str(exc.value)
    assert "HTTP 503" in text
    assert "Try again later" in text


@pytest.mark.asyncio
async def test_error_status_with_json_body_still_raises_http_error():
    """A JSON object on an error status keeps the existing aiohttp behavior."""
    handler = body_handler('{"error": true}', "application/json", status=503)
    async with search_server(handler) as client:
        with pytest.raises(aiohttp.ClientResponseError) as exc:
            await client.search("test")

    assert exc.value.status == 503


@pytest.mark.asyncio
async def test_log_names_the_content_type_and_path_but_not_the_query(caplog):
    """The log carries what the message drops, and still no request data."""
    handler = body_handler("<html>error page</html>", "text/html")
    with caplog.at_level(logging.WARNING, logger="bandcamp_async_api.client"):
        async with search_server(handler) as client:
            with pytest.raises(BandcampUnexpectedResponseError):
                await client.search("private-query")

    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "text/html" in text and SEARCH_PATH in text and "HTTP 200" in text
        for text in messages
    )
    assert not any("private-query" in text for text in messages)


@pytest.mark.asyncio
async def test_log_names_the_requested_path_after_a_redirect(caplog):
    """A redirect to an error page still names the endpoint that was asked for."""

    async def redirect(request):
        raise web.HTTPFound("/api/elsewhere")

    error_page = body_handler("<html>error page</html>", "text/html", status=500)
    with caplog.at_level(logging.WARNING, logger="bandcamp_async_api.client"):
        async with search_server(redirect, [("/api/elsewhere", error_page)]) as client:
            with pytest.raises(BandcampUnexpectedResponseError):
                await client.search("private-query")

    messages = [record.getMessage() for record in caplog.records]
    assert any(SEARCH_PATH in text for text in messages)


@pytest.mark.asyncio
async def test_truncated_body_is_reported_as_unexpected_response(
    mock_session, mock_response
):
    """A body that stops early raises a Bandcamp error, not a payload error."""
    mock_response.status = 200
    mock_response.headers = {}
    mock_response.history = ()
    mock_response.json = AsyncMock(side_effect=aiohttp.ClientPayloadError("incomplete"))
    mock_session.get.return_value.__aenter__.return_value = mock_response
    client = BandcampAPIClient(session=mock_session)

    with pytest.raises(BandcampUnexpectedResponseError) as exc:
        await client.search("test")

    assert isinstance(exc.value.__cause__, aiohttp.ClientPayloadError)


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
