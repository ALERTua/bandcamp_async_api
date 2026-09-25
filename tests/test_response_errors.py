"""Regression tests for unexpected Bandcamp API responses."""

import asyncio
import logging
import time
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
    assert exc.value.status == status
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


def test_unexpected_response_error_builds_without_arguments():
    """The error still builds without a message, like any other exception."""
    error = BandcampUnexpectedResponseError()

    assert str(error) == "The Bandcamp API returned a response that is not usable JSON."
    assert error.status is None


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


@asynccontextmanager
async def slow_search_url(delay, *, in_body=False):
    """Serve a search endpoint that answers, or finishes its body, after `delay` seconds."""

    async def handler(request):
        if not in_body:
            await asyncio.sleep(delay)
            return web.json_response({"results": []})
        response = web.StreamResponse(headers={"Content-Type": "application/json"})
        await response.prepare(request)
        await response.write(b'{"results": ')
        await asyncio.sleep(delay)
        await response.write(b"[]}")
        return response

    app = web.Application()
    app.router.add_get(SEARCH_PATH, handler)
    # Cancel a slow handler once the client hangs up, so shutdown does not wait.
    runner = web.AppRunner(app, handler_cancellation=True)
    await runner.setup()
    try:
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        yield f"http://127.0.0.1:{runner.addresses[0][1]}/api"
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "timeout",
    [
        pytest.param(0.3, id="seconds"),
        pytest.param(aiohttp.ClientTimeout(total=0.3), id="client-timeout"),
    ],
)
async def test_timeout_applies_to_a_passed_in_session(timeout):
    """The client limit cuts a slow answer even on a session without its own limit."""
    async with slow_search_url(delay=5) as base_url, aiohttp.ClientSession() as session:
        client = BandcampAPIClient(session=session, timeout=timeout)
        client.BASE_URL = base_url
        started = time.monotonic()
        with pytest.raises(TimeoutError):
            await client.search("test")
        assert time.monotonic() - started < 2


@pytest.mark.asyncio
async def test_no_timeout_keeps_the_session_limit():
    """Without a client limit the session's own limit still applies."""
    session_timeout = aiohttp.ClientTimeout(total=0.3)
    async with (
        slow_search_url(delay=5) as base_url,
        aiohttp.ClientSession(timeout=session_timeout) as session,
    ):
        client = BandcampAPIClient(session=session)
        client.BASE_URL = base_url
        started = time.monotonic()
        with pytest.raises(TimeoutError):
            await client.search("test")
        assert time.monotonic() - started < 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "timeout",
    [
        pytest.param(aiohttp.ClientTimeout(total=0.3), id="total"),
        pytest.param(aiohttp.ClientTimeout(sock_read=0.3), id="sock-read"),
    ],
)
async def test_slow_body_raises_timeout_not_unexpected_response(timeout):
    """A body that stalls after the headers raises TimeoutError, not a Bandcamp error."""
    async with (
        slow_search_url(delay=2, in_body=True) as base_url,
        BandcampAPIClient(timeout=timeout) as client,
    ):
        client.BASE_URL = base_url
        started = time.monotonic()
        with pytest.raises(TimeoutError):
            await client.search("test")
        assert time.monotonic() - started < 1.5


@pytest.mark.asyncio
async def test_timeout_replaces_the_session_limit():
    """A client limit longer than the session's lets a slow answer through."""
    session_timeout = aiohttp.ClientTimeout(total=0.3)
    async with (
        slow_search_url(delay=1) as base_url,
        aiohttp.ClientSession(timeout=session_timeout) as session,
    ):
        client = BandcampAPIClient(session=session, timeout=5)
        client.BASE_URL = base_url
        assert await client.search("test") == []


@pytest.mark.parametrize(
    "timeout",
    [
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
        pytest.param(float("nan"), id="nan"),
        pytest.param(float("inf"), id="inf"),
    ],
)
def test_timeout_refuses_a_value_that_sets_no_limit(timeout):
    """aiohttp reads these as no limit, or fails at the first request."""
    with pytest.raises(ValueError, match="finite number above 0"):
        BandcampAPIClient(timeout=timeout)


@pytest.mark.parametrize(
    "timeout",
    [
        pytest.param("5", id="string"),
        pytest.param(True, id="bool"),
        pytest.param([5], id="list"),
    ],
)
def test_timeout_refuses_a_value_that_is_no_number(timeout):
    """A string fails only at the first request, and aiohttp reads True as 1 second."""
    with pytest.raises(TypeError, match="timeout must be seconds"):
        BandcampAPIClient(timeout=timeout)


def test_timeout_number_becomes_a_total_limit():
    """A number of seconds becomes a ClientTimeout with only the total set."""
    assert BandcampAPIClient(timeout=2.5).timeout == aiohttp.ClientTimeout(total=2.5)


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
