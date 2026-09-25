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
- **Lyrics**: Fetch song lyrics on request, at the cost of one extra request
- **Artists**: Access artist profiles, discographies, and metadata
- **Collections**: Browse user collections and wishlists (auth required for private data)
- **Following**: Access following bands, following fans, and followers
- **Feed**: Get personalized music feed with new releases from followed artists
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
    async with BandcampAPIClient(
        identity_token='7%09optional_identity_token%7D'
    ) as client:
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

## Timeouts

Each request uses the time limit of the aiohttp session. In aiohttp 3.14, a new session allows 300 seconds per request and 30 seconds for the socket connection. Pass `timeout` to set your own limit, in seconds or as an `aiohttp.ClientTimeout`. The client limit replaces the session limit, also on a session that you pass in. A number sets only the total time, and a `ClientTimeout` field that you leave unset has no limit. The client refuses `0`, a negative number and a value that is not a number.

```python
import aiohttp
from bandcamp_async_api import BandcampAPIClient

# 30 seconds for each request
client = BandcampAPIClient(timeout=30)

# Separate limits for the whole request and for the connection
client = BandcampAPIClient(timeout=aiohttp.ClientTimeout(total=120, sock_connect=10))
```

The limit applies to each request, not to the whole call. One `get_album` call with `with_lyrics=True` can make up to three requests.

When a request runs over the limit, the client raises `TimeoutError`. `TimeoutError` is not a `BandcampAPIError`, so catch it on its own. With `with_lyrics=True`, a lyrics request over the limit does not fail the call, and `track.lyrics` stays `None`. The `get_lyrics`, `get_album_lyrics` and `get_track_lyrics` methods raise `TimeoutError` like every other call.

## Music Feed

The `get_feed()` method retrieves a personalized music feed containing new releases from followed artists, fan purchases, and fan picks. This endpoint requires authentication - you must provide an identity token.

```python
import asyncio
from bandcamp_async_api import BandcampAPIClient, BandcampMustBeLoggedInError


async def main():
    async with BandcampAPIClient(identity_token='your_identity_token') as client:
        # Get your music feed
        feed = await client.get_feed()
        print(f"New stories: {len(feed.stories)}")
        print(f"Has more: {feed.has_more}")

        # Iterate through feed stories
        for story in feed.stories:
            print(f"  - {story.story_type}: {story.item_title} by {story.band_name}")

        # Access tracks with streaming URLs
        for track in feed.track_list:
            print(f"  Track: {track.title} - {track.streaming_url}")

        # Paginate through older stories
        if feed.has_more and feed.oldest_story_date:
            older_feed = await client.get_feed(older_than=feed.oldest_story_date)
            print(f"Older stories: {len(older_feed.stories)}")


if __name__ == '__main__':
    asyncio.run(main())
```

### Feed Story Types

The feed contains different story types:
- `np` - New track/track release
- `nr` - New album release
- `p` - Fan purchase
- `fp` - Fan pick

### Error Handling

The feed endpoint requires authentication. If you try to access it without an identity token, you'll receive a `BandcampMustBeLoggedInError`:

```python
from bandcamp_async_api import BandcampAPIClient, BandcampMustBeLoggedInError


async def safe_get_feed():
    client = BandcampAPIClient()  # No identity token
    try:
        feed = await client.get_feed()
    except BandcampMustBeLoggedInError:
        print("Feed requires authentication - provide an identity token")
```

## Artist vs. performer credit

Bandcamp distinguishes between the **page owner** (the band whose `bandcamp.com` page hosts a release) and the **performer credit** for a specific release. They usually match, but on label-style pages they diverge — e.g. *Mortaja*'s "Combined Minds" is published on `audiophob.bandcamp.com`, so the page owner is `audiophob` and the performer is `Mortaja`.

`BCAlbum` and `BCTrack` expose both:

- `album.artist` (`BCArtist`) — always the page-owning band. Has a Bandcamp profile, follows/following counts, etc.
- `album.tralbum_artist` (`str | None`) — the explicit performer credit from the API. `None` when the API didn't set one (the album is by the band itself).

```python
album = await client.get_album(artist_id, album_id)

# Display name — prefer the performer credit, fall back to the page owner:
display_artist = album.tralbum_artist or album.artist.name

# Detect a label release:
is_label_release = (
    album.tralbum_artist is not None and album.tralbum_artist != album.artist.name
)
```

> **Note (breaking change in `0.2.0`):** prior versions returned the performer credit on `album.artist.name` when present. Consumers that relied on that must read `album.tralbum_artist` instead. The same applies to `BCTrack`.

## Album tracks

`album.tracks` holds every track of the album. An artist can hide a track from streaming, for example on a preorder. Such a track has `streaming_url` set to `None`, but its title, duration, number and page link are set.

```python
album = await client.get_album(artist_id, album_id)
playable = [track for track in album.tracks if track.streaming_url]
```

Each track links to its own page in `track.url`. `track.album_id` and `track.album_title` name the album of the track, also when you get the track with `get_track`. For a standalone track, `album_id` and `album_title` are `None`. `track.art_url` is the cover of the track, which is the album cover unless the track has its own.

`album.total_tracks` comes from `num_downloadable_tracks` in the API answer. It can differ from `len(album.tracks)`. For example, one preorder listed 41 tracks and reported 1.

## Lyrics

Bandcamp does not send the song text together with the track details. It sends a `has_lyrics` flag only. The text lives behind a second request, so this library never fetches it unless you ask for it.

```python
async with BandcampAPIClient() as client:
    # One request. The flag arrives, the text does not.
    track = await client.get_track(2437326710, 178646676)
    print(track.has_lyrics, track.lyrics)  # True None

    # Two requests. The text is filled in.
    track = await client.get_track(2437326710, 178646676, with_lyrics=True)
    print(track.lyrics)

    # One extra request fills every track of the album.
    album = await client.get_album(2437326710, 1994024535, with_lyrics=True)

    # Or ask for the map yourself: track ID to text.
    album_lyrics = await client.get_album_lyrics(1994024535)
    track_lyrics = await client.get_track_lyrics(178646676)
```

`with_lyrics` costs one extra request per call. The client skips that request when no track reports lyrics, so an album without lyrics costs nothing.

`get_album_lyrics` answers for every track of the album with one request. When the id is really a standalone track, the album request answers an empty map, and the client asks again as a track. That costs one more request and covers the same ids that `get_album` resolves through its track fallback.

A failed lyrics request never breaks the call. The track comes back with an empty `lyrics` field, and the client writes a warning to the log.

Bandcamp serves plain text only. There is no timed variant.

## Collections

`get_collection_items` returns the collection, the wishlist or the following lists of a fan. Without `fan_id`, it needs an identity token and reads your own lists. `CollectionType` lives in `bandcamp_async_api.models`.

For collection and wishlist items, `tralbum_type` and `tralbum_id` name the release to fetch. `tralbum_type` is `"a"` for an album and `"t"` for a track. Use `tralbum_id` and not `item_id`, because for a physical release (`item_type` `"package"`) `item_id` names the package.

```python
from bandcamp_async_api import TRALBUM_TYPE_ALBUM
from bandcamp_async_api.models import CollectionType

page = await client.get_collection_items(CollectionType.COLLECTION, fan_id=fan_id)
for item in page.items:
    if item.tralbum_type == TRALBUM_TYPE_ALBUM:
        album = await client.get_album(item.band_id, item.tralbum_id)
    else:
        track = await client.get_track(item.band_id, item.tralbum_id)
```

Each item also carries `art_url`, `band_url`, `is_preorder`, `album_id` and `album_title`. `album_id` is `None` for a standalone track. The featured track of the release is in `featured_track`, `featured_track_title`, `featured_track_duration` and `featured_track_number`.

## API Reference

### Core Client

- `BandcampAPIClient(session=None, identity_token=None, ..., timeout=None)` - Main API client, see [Timeouts](#timeouts)
- `search(query: str)` - Search Bandcamp
- `get_album(artist_id, album_id, *, with_lyrics=False)` - Get album details
- `get_track(artist_id, track_id, *, with_lyrics=False)` - Get track details
- `get_lyrics(tralbum_id, tralbum_type)` - Get lyrics as a track ID to text map; the type constants `TRALBUM_TYPE_ALBUM` and `TRALBUM_TYPE_TRACK` are exported
- `get_album_lyrics(album_id)` - Get the lyrics of every album track in one request
- `get_track_lyrics(track_id)` - Get the lyrics of a standalone track
- `get_artist(artist_id)` - Get artist details
- `get_collection_summary()` - Get collection overview
- `get_collection_items(collection_type, older_than_token, count, fan_id)` - Get collection/wishlist/following items with pagination
- `get_artist_discography(artist_id)` - Get artist's complete discography
- `get_feed(older_than)` - Get personalized music feed with pagination support

### Data Models

- `SearchResultItem` - Base search result
- `BCAlbum` - Album with tracks and metadata
- `BCTrack` - Individual track information
- `BCArtist` - Artist/band profile
- `CollectionSummary` - User's collection data
- `CollectionItem` - Individual collection item
- `FollowingItem` - Band/artist from following list
- `FanItem` - Fan/user from following_fans or followers
- `FeedResponse` - User's music feed with stories and tracks
- `FeedStory` - Individual feed story (new release, fan purchase, etc.)
- `FeedTrack` - Track from feed with streaming URL
- `FeedBandInfo` - Band information referenced in feed
- `FeedFanInfo` - Fan information referenced in feed

### Exceptions

- `BandcampAPIError` - Base API error
- `BandcampNotFoundError` - Resource not found
- `BandcampBadQueryError` - Invalid search query
- `BandcampRateLimitError` - Rate limit exceeded (includes `retry_after` attribute)
- `BandcampMustBeLoggedInError` - The request needs an identity token
- `BandcampUnexpectedResponseError` - Bandcamp answered with something that is not usable JSON (includes `status` attribute)

## Error Handling

The client provides specific exception types for different error conditions:

```python
from bandcamp_async_api import (
    BandcampAPIClient,
    BandcampNotFoundError,
    BandcampAPIError,
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

When Bandcamp answers with something the client cannot use, such as an HTML error page or an empty body, the client raises `BandcampUnexpectedResponseError`. The message carries no request data, so you can show it to a user. The client logs the status, the path and the content type at the warning level. When aiohttp itself rejected the body, the chained cause also keeps the full request URL.

The `status` attribute of `BandcampUnexpectedResponseError` holds the HTTP status, for example 503. For a 4xx status, the message does not ask you to try again, because that answer repeats on every retry. For any other status, the message asks you to try again later.

A failing HTTP status whose body is a JSON object still raises `aiohttp.ClientResponseError`. A network failure raises another `aiohttp.ClientError`, and a request over the time limit raises `TimeoutError`. None of them is a `BandcampAPIError`, so catch `aiohttp.ClientError` and `TimeoutError` too if you want one handler for every failure.

### Rate Limiting

When Bandcamp's API rate limit is exceeded, a `BandcampRateLimitError` is raised with a `retry_after` attribute indicating how many seconds to wait before retrying:

```python
import asyncio
from bandcamp_async_api import BandcampAPIClient, BandcampRateLimitError


async def get_album_with_retry(client, artist_id, album_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.get_album(artist_id, album_id)
        except BandcampRateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = e.retry_after or 30
                print(f"Rate limited. Waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                raise
```

For automatic retries with exponential backoff, you can use the `tenacity` library:

```python
from tenacity import retry, retry_if_exception_type, wait_exponential
from bandcamp_async_api import BandcampAPIClient, BandcampRateLimitError


@retry(
    retry=retry_if_exception_type(BandcampRateLimitError),
    wait=wait_exponential(multiplier=1, min=30, max=300),
)
async def get_album(client, artist_id, album_id):
    return await client.get_album(artist_id, album_id)
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
