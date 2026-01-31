"""Bandcamp API Client - standalone async client."""

from typing import Any
from time import time

import aiohttp

from .models import (
    BCAlbum,
    BCArtist,
    BCTrack,
    CollectionSummary,
    SearchResultItem,
    CollectionType,
)
from .parsers import BandcampParsers


class BandcampAPIError(Exception):
    """Base exception for Bandcamp API errors."""


class BandcampNotFoundError(BandcampAPIError):
    """Exception raised when a resource is not found."""


class BandcampBadQueryError(BandcampAPIError):
    """Exception raised when a search query is wrong."""


class BandcampMustBeLoggedInError(BandcampAPIError):
    """Exception raised when identity token is missing or invalid."""


class BandcampAPIClient:
    """Async Bandcamp API client - standalone, no external dependencies."""

    BASE_URL = "https://bandcamp.com/api"

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        identity_token: str | None = None,
        user_agent: str = "bandcamp-api/1.0",
    ):
        """Initialize the Bandcamp API client.

        Args:
            session: Optional aiohttp ClientSession. If not provided, one will be created.
            identity_token: Optional identity token for collection access.
            user_agent: User agent string to use for requests.
        """
        self._session = session
        self._session_overridden = session is not None
        self.identity = identity_token
        self.headers: dict[str, Any] = {"User-Agent": user_agent}
        self._fan_id: int | None = None
        self._parsers = BandcampParsers()

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = self._session or aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if not self._session_overridden and self._session:
            await self._session.close()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have a session, create if needed."""
        self._session = self._session or aiohttp.ClientSession()
        return self._session

    def _process_json_responce(self, resp_json: dict[str, Any]) -> dict[str, Any]:
        # Check for Bandcamp API errors
        if isinstance(resp_json, dict) and "error" in resp_json:
            if "No such" in resp_json.get("error_message", ""):
                raise BandcampNotFoundError(resp_json["error_message"])
            elif "bad query" in resp_json.get("error_message", ""):
                raise BandcampBadQueryError(resp_json["error_message"])
            elif "must be logged in" in resp_json.get("error_message", ""):
                raise BandcampMustBeLoggedInError(resp_json["error_message"])
            raise BandcampAPIError(resp_json)

        return resp_json

    async def _request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        session = await self._ensure_session()

        # Add identity cookie if available
        headers = dict(self.headers)
        if self.identity:
            headers["Cookie"] = f"identity={self.identity}"
        kwargs['headers'] = headers

        # Dynamically call the appropriate method (get, post, etc.)
        request_method = getattr(session, method.lower())
        async with request_method(url, **kwargs) as resp:
            resp.raise_for_status()
            resp_json = await resp.json()

            return self._process_json_responce(resp_json)

    async def _get(self, **kwargs) -> dict[str, Any]:
        """Make GET request and handle common error cases."""
        kwargs['method'] = 'GET'
        return await self._request(**kwargs)

    async def _post(self, **kwargs) -> dict[str, Any]:
        """Make POST request and handle common error cases."""
        kwargs['method'] = 'POST'
        return await self._request(**kwargs)

    async def search(self, query: str) -> list[SearchResultItem]:
        """Search Bandcamp for artists, albums, and tracks.

        Args:
            query: Search query string.

        Returns:
            List of search result items.
        """
        url = f"{self.BASE_URL}/fuzzysearch/1/app_autocomplete"
        # Replace commas with spaces to avoid "too many q terms" API error
        sanitized_query = query.replace(",", " ")
        params = {"q": sanitized_query, "param_with_locations": "true"}

        data = await self._get(url=url, params=params)
        results = data.get("results", [])

        output = [self._parsers.parse_search_result_item(item) for item in results]
        return [_ for _ in output if _]

    async def get_album(self, artist_id: int | str, album_id: int | str) -> BCAlbum:
        """Get album details by artist and album ID.

        Args:
            artist_id: Bandcamp artist/band ID.
            album_id: Bandcamp album ID.

        Returns:
            Album object with full details.
        """
        url = f"{self.BASE_URL}/mobile/24/tralbum_details"
        params = {"band_id": artist_id, "tralbum_id": album_id, "tralbum_type": "a"}

        try:
            data = await self._get(url=url, params=params)
        except BandcampNotFoundError:
            # Try as a single track instead
            params["tralbum_type"] = "t"
            data = await self._get(url=url, params=params)

        return self._parsers.parse_album(data)

    async def get_track(self, artist_id: int | str, track_id: int | str) -> BCTrack:
        """Get track details by artist and track ID.

        Args:
            artist_id: Bandcamp artist/band ID.
            track_id: Bandcamp track ID.

        Returns:
            Track object with full details.
        """
        url = f"{self.BASE_URL}/mobile/24/tralbum_details"
        params = {"band_id": artist_id, "tralbum_id": track_id, "tralbum_type": "t"}

        data = await self._get(url=url, params=params)
        return self._parsers.parse_track(data)

    async def get_artist(self, artist_id: int | str) -> BCArtist:
        """Get artist/band details by ID.

        Args:
            artist_id: Bandcamp artist/band ID.

        Returns:
            Artist object with full details.
        """
        url = f"{self.BASE_URL}/mobile/24/band_details"
        data = await self._post(url=url, json={"band_id": artist_id})
        return self._parsers.parse_artist(data)

    async def get_collection_summary(self) -> CollectionSummary:
        """Get user's collection summary (requires identity token).

        Returns:
            CollectionSummary with basic collection info.

        Raises:
            BandcampMustBeLoggedInError: If identity token is not set.
        """
        if not self.identity:
            raise BandcampMustBeLoggedInError(
                "You must be logged in to access collection data"
            )

        url = f"{self.BASE_URL}/fan/2/collection_summary"
        data = await self._get(url=url)

        self._fan_id: int = data.get("fan_id")
        return CollectionSummary(
            fan_id=self._fan_id,
            items=[],  # Summary doesn't include items
            has_more=False,
        )

    async def get_collection_items(
        self,
        collection_type: CollectionType = CollectionType.COLLECTION,
        older_than_token: str | None = None,
        count: int = 50,
    ) -> CollectionSummary:
        """Get collection items (requires identity token).

        Args:
            collection_type: Collection type (COLLECTION, WISHLIST, or FOLLOWING).
            older_than_token: Token for pagination.
            count: Number of items to fetch.

        Returns:
            CollectionSummary with items.

        Raises:
            BandcampMustBeLoggedInError: If identity token is not set.
        """
        if not self.identity:
            raise BandcampMustBeLoggedInError(
                "You must be logged in to access collection data"
            )

        if self._fan_id is None:
            await self.get_collection_summary()

        if older_than_token is None:
            older_than_token = str(time()) + ":0:a::"

        url = f"{self.BASE_URL}/fancollection/1/{collection_type.value}"

        data = {
            "fan_id": self._fan_id,
            "older_than_token": older_than_token,
            "count": count,
        }

        response_data = await self._post(url=url, json=data)

        items = [
            self._parsers.parse_collection_item(item)
            for item in response_data.get("items", [])
        ]

        return CollectionSummary(
            fan_id=self._fan_id,  # ty:ignore[invalid-argument-type]
            items=items,
            has_more=response_data.get("has_more", False),
            last_token=response_data.get("last_token"),
        )

    async def get_artist_discography(
        self, artist_id: int | str
    ) -> list[dict[str, Any]]:
        """Get artist's discography (albums and tracks).

        API: GET /api/band/3/discography
        Alternative: GET /api/mobile/24/band_details (used due to better data)

        Args:
            artist_id: Bandcamp artist/band ID.

        Returns:
            List of discography items with type and IDs.
        """
        # Note: Using mobile/24/band_details instead of band/3/discography
        # because it provides more complete data including tracks
        artist_data = await self._post(
            url=f"{self.BASE_URL}/mobile/24/band_details", json={"band_id": artist_id}
        )

        return artist_data.get("discography", [])
