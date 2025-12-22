"""Real data tests for search and data retrieval methods.

These tests require BANDCAMP_IDENTITY_TOKEN environment variable to be set.
Tests are marked as manual and should be run explicitly with:
    pytest -m manual tests/real_data/

Run with: pytest -m manual tests/real_data/test_search_and_retrieval.py -v
"""

import pytest

from bandcamp_async_api.client import BandcampBadQueryError

from .constants import (
    TEST_ARTIST_NAME,
    TEST_ALBUM_NAME,
    TEST_TRACK_NAME,
    TEST_SEARCH_QUERY,
)


# Manual test marker
manual = pytest.mark.manual


class TestSearchAndRetrievalRealData:
    """Test search and data retrieval methods with real Bandcamp data."""

    @pytest.fixture(autouse=True)
    async def setup_client(self, bc_api_client):
        """Set up API client with identity token if available."""
        self.client = bc_api_client

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_multiple_types(self):
        """Test search returns multiple result types (artist, album, track)."""
        # Search for something that might return multiple types
        results = await self.client.search(TEST_SEARCH_QUERY)

        assert len(results) > 0, (
            f"Search should return results for '{TEST_SEARCH_QUERY}'"
        )

        # Check we have different types
        result_types = {r.type for r in results}
        print(f"Search for '{TEST_SEARCH_QUERY}' returned {len(results)} results")
        print(f"Result types found: {result_types}")

        # Should have at least artists and albums for this query
        assert "artist" in result_types or "album" in result_types, (
            f"Search should return artists or albums for '{TEST_SEARCH_QUERY}'"
        )

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_artists_only(self):
        """Test search filtering for artists only."""
        results = await self.client.search(TEST_ARTIST_NAME)

        assert len(results) > 0, (
            f"Search should return results for '{TEST_ARTIST_NAME}'"
        )

        # Filter for artists
        artist_results = [r for r in results if r.type == "artist"]
        assert len(artist_results) > 0, f"Should find artists for '{TEST_ARTIST_NAME}'"

        print(f"Found {len(artist_results)} artists for '{TEST_ARTIST_NAME}':")
        for i, artist in enumerate(artist_results[:5]):
            print(f"  {i + 1}. {artist.name} (ID: {artist.id})")
            if hasattr(artist, 'location') and artist.location:
                print(f"     Location: {artist.location}")
            if hasattr(artist, 'tags') and artist.tags:
                print(f"     Tags: {', '.join(artist.tags[:3])}")

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_albums_only(self):
        """Test search filtering for albums only."""
        results = await self.client.search(TEST_ALBUM_NAME)

        assert len(results) > 0, f"Search should return results for '{TEST_ALBUM_NAME}'"

        # Filter for albums
        album_results = [r for r in results if r.type == "album"]
        assert len(album_results) > 0, f"Should find albums for '{TEST_ALBUM_NAME}'"

        print(f"Found {len(album_results)} albums for '{TEST_ALBUM_NAME}':")
        for i, album in enumerate(album_results[:5]):
            print(f"  {i + 1}. {album.name} by {album.artist_name} (ID: {album.id})")
            if hasattr(album, 'artist_name'):
                print(f"     Artist: {album.artist_name}")

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_tracks_only(self):
        """Test search filtering for tracks only."""
        results = await self.client.search(TEST_TRACK_NAME)

        assert len(results) > 0, f"Search should return results for '{TEST_TRACK_NAME}'"

        # Filter for tracks
        track_results = [r for r in results if r.type == "track"]
        assert len(track_results) > 0, f"Should find tracks for '{TEST_TRACK_NAME}'"

        print(f"Found {len(track_results)} tracks for '{TEST_TRACK_NAME}':")
        for i, track in enumerate(track_results[:5]):
            print(f"  {i + 1}. {track.name} by {track.artist_name} (ID: {track.id})")
            if hasattr(track, 'album_name') and track.album_name:
                print(f"     Album: {track.album_name}")

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_case_sensitivity(self):
        """Test search case sensitivity."""
        # Test lowercase
        lower_results = await self.client.search(TEST_ARTIST_NAME.lower())
        # Test uppercase
        upper_results = await self.client.search(TEST_ARTIST_NAME.upper())

        print(f"Lowercase search: {len(lower_results)} results")
        print(f"Uppercase search: {len(upper_results)} results")

        # Should find similar results (case insensitive search)
        assert len(lower_results) > 0, "Lowercase search should work"
        assert len(upper_results) > 0, "Uppercase search should work"

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_partial_matches(self):
        """Test search with partial artist name."""
        # Search for just "Path" from "Pathos"
        partial_results = await self.client.search("Path")

        print(f"Partial search for 'Path': {len(partial_results)} results")

        # Should find Pathos
        if len(partial_results) > 0:
            found_pathos = any("pathos" in r.name.lower() for r in partial_results)
            print(f"Found Pathos in partial results: {found_pathos}")

            if found_pathos:
                pathos_result = next(
                    r for r in partial_results if "pathos" in r.name.lower()
                )
                print(f"Pathos match: {pathos_result.name} (ID: {pathos_result.id})")
        else:
            print("No results for partial search")

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_empty_query(self):
        """Test search with empty query."""
        # Test empty string - should raise BandcampBadQueryError
        with pytest.raises(BandcampBadQueryError):
            await self.client.search("")

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_special_characters(self):
        """Test search with special characters."""
        # Test with special characters that might be in titles
        special_query = TEST_TRACK_NAME  # Has apostrophe and spaces
        results = await self.client.search(special_query)

        print(f"Special character search '{special_query}': {len(results)} results")
        assert isinstance(results, list), "Search with special chars should return list"

        if len(results) > 0:
            for i, result in enumerate(results[:3]):
                print(f"  {i + 1}. {result.name} ({result.type})")

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_unicode_characters(self):
        """Test search with unicode/non-ASCII characters."""
        # Test with unicode characters
        unicode_query = "αβγδε"  # Greek letters
        results = await self.client.search(unicode_query)

        print(f"Unicode search '{unicode_query}': {len(results)} results")
        assert isinstance(results, list), "Unicode search should return list"

        # Most likely no results, but shouldn't crash
        if len(results) > 0:
            for i, result in enumerate(results[:3]):
                print(f"  {i + 1}. {result.name} ({result.type})")

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_result_consistency(self):
        """Test that search results are consistent across multiple calls."""
        # Make same search twice
        results1 = await self.client.search(TEST_ARTIST_NAME)
        results2 = await self.client.search(TEST_ARTIST_NAME)

        print(f"First search: {len(results1)} results")
        print(f"Second search: {len(results2)} results")

        # Should get similar number of results
        assert abs(len(results1) - len(results2)) <= 2, (
            "Search results should be consistent between calls"
        )

        # Get IDs for comparison
        ids1 = {r.id for r in results1}
        ids2 = {r.id for r in results2}

        # Should have significant overlap
        overlap = len(ids1.intersection(ids2))
        print(f"Result overlap: {overlap} / {min(len(results1), len(results2))}")

        # At least 50% overlap expected
        min_expected = min(len(results1), len(results2)) // 2
        assert overlap >= min_expected, "Search results should have significant overlap"

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_data_structure_validation(self):
        """Test detailed validation of search result data structures."""
        results = await self.client.search(TEST_ARTIST_NAME)

        if len(results) == 0:
            print("No search results to validate")
            return

        # Take first result for detailed validation
        result = results[0]

        print(f"Validating search result: {result.name}")

        # Validate all required fields
        assert hasattr(result, 'type'), "Missing type"
        assert hasattr(result, 'id'), "Missing id"
        assert hasattr(result, 'name'), "Missing name"
        assert hasattr(result, 'url'), "Missing url"

        print(f"  Type: {result.type}")
        print(f"  ID: {result.id}")
        print(f"  Name: {result.name}")
        print(f"  URL: {result.url}")

        # Validate type-specific fields
        if result.type == "artist":
            assert hasattr(result, 'location'), "Artist should have location"
            assert hasattr(result, 'is_label'), "Artist should have is_label"
            assert hasattr(result, 'tags'), "Artist should have tags"
            print(f"  Location: {getattr(result, 'location', 'Unknown')}")
            print(f"  Is label: {getattr(result, 'is_label', False)}")
            print(f"  Tags: {getattr(result, 'tags', [])}")

        elif result.type == "album":
            assert hasattr(result, 'artist_id'), "Album should have artist_id"
            assert hasattr(result, 'artist_name'), "Album should have artist_name"
            print(f"  Artist ID: {getattr(result, 'artist_id', 'Unknown')}")
            print(f"  Artist name: {getattr(result, 'artist_name', 'Unknown')}")

        elif result.type == "track":
            assert hasattr(result, 'artist_id'), "Track should have artist_id"
            assert hasattr(result, 'artist_name'), "Track should have artist_name"
            assert hasattr(result, 'album_name'), "Track should have album_name"
            print(f"  Artist ID: {getattr(result, 'artist_id', 'Unknown')}")
            print(f"  Artist name: {getattr(result, 'artist_name', 'Unknown')}")
            print(f"  Album name: {getattr(result, 'album_name', 'Unknown')}")
