"""Real data tests for Bandcamp collection methods.

These tests require BANDCAMP_IDENTITY_TOKEN environment variable to be set.
Tests are marked as manual and should be run explicitly with:
    pytest -m manual tests/real_data/

Run with: pytest -m manual tests/real_data/test_collection_methods.py -v
"""

import pytest

from bandcamp_async_api.client import CollectionType
from bandcamp_async_api.models import CollectionSummary, CollectionItem


# Manual test marker
manual = pytest.mark.manual


class TestCollectionMethodsRealData:
    """Test collection-related API methods with real Bandcamp data."""

    @pytest.fixture(autouse=True)
    async def setup_client(self, bc_api_client):
        """Set up API client with identity token if available."""
        self.client = bc_api_client

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_get_collection_summary(self):
        """Test getting collection summary."""
        summary = await self.client.get_collection_summary()

        assert isinstance(summary, CollectionSummary), (
            f"Expected CollectionSummary, got {type(summary)}"
        )
        assert summary.fan_id > 0, "Fan ID should be positive"
        assert isinstance(summary.items, list), "Items should be a list"

        print(f"Collection summary for fan ID: {summary.fan_id}")
        print(f"Items count: {len(summary.items)}")
        print(f"Has more: {summary.has_more}")

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_get_collection_items(self):
        """Test getting collection items."""
        limit = 5
        summary = await self.client.get_collection_items(
            collection_type=CollectionType.COLLECTION, count=limit
        )

        assert isinstance(summary, CollectionSummary), (
            f"Expected CollectionSummary, got {type(summary)}"
        )
        assert len(summary.items) <= limit, (
            "Should not return more than requested items"
        )

        print(f"Found {len(summary.items)} collection items")

        # Print first few items for verification
        for i, item in enumerate(summary.items):
            print(f"Item {i + 1}: {item.item_title} by {item.band_name}")
            print(f"  Type: {item.item_type}, ID: {item.item_id}")
            print(f"  Purchasable: {item.is_purchasable}")
            if item.price:
                print(f"  Price: {item.price}")

        # Validate item structure
        for item in summary.items:
            assert isinstance(item, CollectionItem), (
                f"Expected CollectionItem, got {type(item)}"
            )
            assert item.item_title, "Item should have title"
            assert item.band_name, "Item should have band name"
            assert item.item_type in ["album", "track", "band"], (
                f"Invalid item type: {item.item_type}"
            )

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_get_wishlist_items(self):
        """Test getting wishlist items."""
        limit = 5
        summary = await self.client.get_collection_items(
            collection_type=CollectionType.WISHLIST, count=limit
        )

        assert isinstance(summary, CollectionSummary), (
            f"Expected CollectionSummary, got {type(summary)}"
        )
        assert len(summary.items) <= limit, (
            "Should not return more than requested items"
        )

        print(f"Found {len(summary.items)} wishlist items")

        # Print wishlist items for verification
        for i, item in enumerate(summary.items):
            print(f"Wishlist item {i + 1}: {item.item_title} by {item.band_name}")
            print(f"  Type: {item.item_type}, ID: {item.item_id}")

        # Validate wishlist items
        for item in summary.items:
            assert isinstance(item, CollectionItem), (
                f"Expected CollectionItem, got {type(item)}"
            )
            assert item.item_title, "Wishlist item should have title"

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_get_following_bands(self):
        """Test getting followed bands."""
        limit = 5
        summary = await self.client.get_collection_items(
            collection_type=CollectionType.FOLLOWING, count=limit
        )

        assert isinstance(summary, CollectionSummary), (
            f"Expected CollectionSummary, got {type(summary)}"
        )
        assert len(summary.items) <= limit, (
            "Should not return more than requested items"
        )

        print(f"Found {len(summary.items)} followed bands")

        # Print followed bands for verification
        for i, item in enumerate(summary.items):
            print(f"Followed band {i + 1}: {item.band_name}")
            print(f"  ID: {item.band_id}")
            print(f"  URL: {item.item_url}")

        # Validate following items
        for item in summary.items:
            assert isinstance(item, CollectionItem), (
                f"Expected CollectionItem, got {type(item)}"
            )
            assert item.item_type == "band", (
                f"Following items should be type 'band', got {item.item_type}"
            )

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_collection_pagination(self):
        """Test collection pagination with smaller chunks."""
        # Get first page
        first_page = await self.client.get_collection_items(
            collection_type=CollectionType.COLLECTION, count=5
        )

        if first_page.has_more and len(first_page.items) > 0:
            print(
                f"First page has {len(first_page.items)} items, has_more={first_page.has_more}"
            )

            # Get second page using last_token
            if first_page.last_token:
                second_page = await self.client.get_collection_items(
                    collection_type=CollectionType.COLLECTION,
                    count=5,
                    older_than_token=first_page.last_token,
                )

                print(f"Second page has {len(second_page.items)} items")

                # Verify pagination worked (items should be different)
                first_ids = {item.item_id for item in first_page.items}
                second_ids = {item.item_id for item in second_page.items}

                # Should have minimal overlap (only possible if very small collection)
                overlap = first_ids.intersection(second_ids)
                print(f"Items overlap between pages: {len(overlap)}")

                assert len(overlap) <= 1, "Too much overlap between pages"
            else:
                print("No pagination token available")
        else:
            print("No pagination needed - all items fit in first page")

    @manual
    @pytest.mark.asyncio(loop_scope="session")
    async def test_collection_data_structure(self):
        """Test detailed validation of collection item data structures."""
        summary = await self.client.get_collection_items(
            collection_type=CollectionType.COLLECTION, count=10
        )

        if len(summary.items) == 0:
            print("No collection items to validate")
            return

        # Take first item for detailed validation
        item = summary.items[0]

        print(f"Validating collection item: {item.item_title}")

        # Validate all required fields
        assert hasattr(item, 'item_type'), "Missing item_type"
        assert hasattr(item, 'item_id'), "Missing item_id"
        assert hasattr(item, 'band_id'), "Missing band_id"
        assert hasattr(item, 'band_name'), "Missing band_name"
        assert hasattr(item, 'item_title'), "Missing item_title"
        assert hasattr(item, 'item_url'), "Missing item_url"

        print(f"  Item type: {item.item_type}")
        print(f"  Item ID: {item.item_id}")
        print(f"  Band ID: {item.band_id}")
        print(f"  Band name: {item.band_name}")
        print(f"  Item title: {item.item_title}")
        print(f"  Item URL: {item.item_url}")

        # Validate optional fields
        if hasattr(item, 'art_id') and item.art_id:
            assert isinstance(item.art_id, int), "art_id should be integer"
            print(f"  Art ID: {item.art_id}")

        if hasattr(item, 'is_purchasable'):
            assert isinstance(item.is_purchasable, bool), (
                "is_purchasable should be boolean"
            )
            print(f"  Purchasable: {item.is_purchasable}")

        if hasattr(item, 'price') and item.price:
            assert isinstance(item.price, float), "price should be float"
            print(f"  Price: {item.price}")
