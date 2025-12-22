# Real Data Tests

This directory contains tests that run against the live Bandcamp API with real data.

## Purpose

These tests validate that the Bandcamp API client works correctly with:
- Real Bandcamp data (Pathos artist, Rapture album, etc.)
- Real authentication via BANDCAMP_IDENTITY_TOKEN
- Real API responses and error conditions
- Actual data relationships (artist → album → track)

## Setup

### Required Environment Variable

Set your Bandcamp identity token:

```bash
export BANDCAMP_IDENTITY_TOKEN="your_identity_token_here"
```

### Getting Identity Token

1. Log into your Bandcamp account
2. Open browser developer tools
3. Look for `identity` cookie value
4. Copy the token value and set as environment variable

## Running Tests

### Run All Real Data Tests

```bash
pytest -m manual tests/real_data/ -v
```

### Run Specific Test Files

```bash
# Main API methods (search, get_artist, get_album, get_track, etc.)
pytest -m manual tests/real_data/test_main_api.py -v

# Collection methods (requires authentication)
pytest -m manual tests/real_data/test_collection_methods.py -v

# Search and data retrieval methods
pytest -m manual tests/real_data/test_search_and_retrieval.py -v
```

### Run Individual Tests

```bash
# Run specific test method
pytest -m manual tests/real_data/test_main_api.py::TestMainAPIRealData::test_search_artist -v
```

## Test Data

Tests use these constants:

- **TEST_ARTIST**: "Pathos"
- **TEST_ALBUM**: "Rapture" (album by Pathos)
- **TEST_SONG**: "I Don't Dream With Gods" (track from Rapture album)
- **TEST_ALBUM_URL**: "https://pathos.bandcamp.com/album/rapture"

This creates a validation chain: Artist → Album → Track

## Test Coverage

### Main API Methods (`test_main_api.py`)
- Search for artist, album, track
- Get detailed artist information
- Get detailed album information (with track listing)
- Get detailed track information
- Get artist discography
- Error handling for invalid IDs
- Rate limit handling (429 errors)

### Collection Methods (`test_collection_methods.py`)
- Collection summary (requires auth)
- Collection items with pagination
- Wishlist items
- Followed bands
- Authentication requirement validation
- Data structure validation
- Rate limit handling

### Search and Retrieval (`test_search_and_retrieval.py`)
- Multiple result types (artist/album/track)
- Case sensitivity testing
- Partial name matching
- Special character handling
- Unicode character support
- Search result consistency
- Data structure validation
- Performance baseline
- Empty query handling

## Important Notes

⚠️ **These tests make real API calls**

- They will consume your Bandcamp rate limits
- They require valid authentication credentials
- They make external network requests
- They may fail due to API issues outside our control

⚠️ **Manual-only execution**

- Tests are marked with `@pytest.mark.manual`
- They won't run with normal `pytest` command
- Must use `-m manual` flag explicitly
- This prevents accidental API consumption in CI/automated testing

## Rate Limit Handling

Tests include basic 429 rate limit detection as requested. For production use, consider implementing:

- Exponential backoff retry logic
- Request rate limiting (e.g., 1 request/second)
- Proper error handling and user feedback

## Troubleshooting

### Common Issues

1. **"BANDCAMP_IDENTITY_TOKEN environment variable not set"**
   - Export the environment variable as shown above

2. **Tests fail with network errors**
   - Check internet connection
   - Verify Bandcamp is accessible
   - Try again later (rate limiting)

3. **Search returns no results**
   - Bandcamp may have changed their data
   - Try with different search terms
   - Verify test constants are still valid

4. **Rate limit errors**
   - Wait before running tests again
   - Run tests in smaller batches
   - Consider running tests at different times
