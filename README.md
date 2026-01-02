[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner-direct-single.svg)](https://stand-with-ukraine.pp.ua)
[![Made in Ukraine](https://img.shields.io/badge/made_in-Ukraine-ffd700.svg?labelColor=0057b7)](https://stand-with-ukraine.pp.ua)
[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/badges/StandWithUkraine.svg)](https://stand-with-ukraine.pp.ua)
[![Russian Warship Go Fuck Yourself](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/badges/RussianWarship.svg)](https://stand-with-ukraine.pp.ua)

# Bandcamp Async API

A modern, asynchronous Python client for the Bandcamp API.

###### This project was created to [implement](https://github.com/music-assistant/server/pull/2871) a Bandcamp music provider for [Music Assistant](https://github.com/music-assistant), enabling seamless integration of Bandcamp's music catalog into home audio systems.

- **Repository**: https://github.com/ALERTua/bandcamp_async_api
- **Changelog**: https://github.com/ALERTua/bandcamp_async_api/releases
- **PyPI**: https://pypi.org/project/bandcamp_async_api/
- **Music Assistant**: https://github.com/music-assistant

## Features

- **Search**: Search for artists, albums, and tracks across Bandcamp
- **Albums**: Retrieve detailed album information including track listings
- **Tracks**: Get individual track details and streaming information
- **Artists**: Access artist profiles, discographies, and metadata
- **Collections**: Browse user collections (requires authentication)
- **Async**: Fully asynchronous API using aiohttp
- **Type-safe**: Complete type hints for all models and methods
- **Well-tested**: Comprehensive test suite with real API data

## Installation

Install from PyPI:

```bash
pip install bandcamp-async-api
```

Or using uv:

```bash
uv add bandcamp-async-api
```

## Quick Start

```python
import asyncio
from bandcamp_async_api import BandcampAPIClient

async def main():
    async with BandcampAPIClient(identity_token='7%09optional_identity_token%7D') as client:
        # Search for music
        results = await client.search("radiohead")
        print(f"Found {len(results)} results")

        # Get album details
        if results:
            album_result = next(r for r in results if r.type == "album")
            album = await client.get_album(album_result.artist_id, album_result.id)
            print(f"Album: {album.title} by {album.artist.name}")

        # Get artist information
        artist_result = next(r for r in results if r.type == "artist")
        artist = await client.get_artist(artist_result.id)
        print(f"Artist: {artist.name} - {artist.bio}")

if __name__ == '__main__':
    asyncio.run(main())
```

## Authentication

For accessing user collections, you need to obtain an identity token from Bandcamp cookies:

```python
from bandcamp_async_api import BandcampAPIClient

client = BandcampAPIClient(identity_token="your_identity_token")
```

## API Reference

### Core Client

- `BandcampAPIClient()` - Main API client
- `search(query: str)` - Search Bandcamp
- `get_album(artist_id, album_id)` - Get album details
- `get_track(artist_id, track_id)` - Get track details
- `get_artist(artist_id)` - Get artist details
- `get_collection_summary()` - Get collection overview
- `get_collection_items()` - Get collection items with pagination
- `get_artist_discography(artist_id)` - Get artist's complete discography

### Data Models

- `SearchResultItem` - Base search result
- `BCAlbum` - Album with tracks and metadata
- `BCTrack` - Individual track information
- `BCArtist` - Artist/band profile
- `CollectionSummary` - User's collection data
- `CollectionItem` - Individual collection item

### Exceptions

- `BandcampAPIError` - Base API error
- `BandcampNotFoundError` - Resource not found
- `BandcampBadQueryError` - Invalid search query

## Error Handling

The client provides specific exception types for different error conditions:

```python
from bandcamp_async_api import (
    BandcampAPIClient,
    BandcampNotFoundError,
    BandcampAPIError
)

async def safe_get_album(client, artist_id, album_id):
    try:
        return await client.get_album(artist_id, album_id)
    except BandcampNotFoundError:
        print("Album not found")
        return None
    except BandcampAPIError as e:
        print(f"API error: {e}")
        return None
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/ALERTua/bandcamp_async_api.git
cd bandcamp_async_api

# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check
```

### Testing

The project includes comprehensive tests:

```bash
# Run all tests
uv run pytest

# Run integration tests (requires real API access)
echo "BANDCAMP_IDENTITY_TOKEN=7%09identity_token%7D" > .env
uv run pytest tests/real_data/
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request


This project is built based on data from:
- https://github.com/michaelherger/Bandcamp-API
- https://github.com/impliedchaos/mopidy-bandcamp
