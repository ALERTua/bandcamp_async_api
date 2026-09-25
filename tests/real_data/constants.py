"""Constants for real data testing."""

# Test data for real API calls
TEST_ARTIST_NAME = "MICROMECHA"
TEST_ARTIST_ID = 468094912
TEST_ALBUM_NAME = "Mecha Cuts Vol.1"
TEST_ALBUM_ID = 1897282681
TEST_TRACK_NAME = "Wakizashi 脇差"
TEST_TRACK_ID = 2489378877
TEST_ARTIST_URL = "https://micromecha.bandcamp.com"
TEST_ALBUM_URL = "https://micromecha.bandcamp.com/album/mecha-cuts-vol-1"

# Additional test queries
TEST_SEARCH_QUERY = "electronic ambient"

# Test data for lyrics calls
TEST_LYRICS_ARTIST_ID = 2437326710  # https://americanforrest.bandcamp.com
TEST_LYRICS_TRACK_ID = (
    178646676  # https://americanforrest.bandcamp.com/track/hold-the-center
)
TEST_LYRICS_ALBUM_ID = (
    1994024535  # https://americanforrest.bandcamp.com/album/salvation-rose-2
)

# An album with tracks hidden from streaming: 6 of 20 on 2026-09-24
TEST_HIDDEN_ARTIST_ID = 2697491130  # https://bonobomusic.bandcamp.com
TEST_HIDDEN_ALBUM_ID = (
    1107540496  # https://bonobomusic.bandcamp.com/album/distance-in-static
)
TEST_HIDDEN_TRACK_ID = (
    1217796510  # https://bonobomusic.bandcamp.com/track/fire-on-the-water-instrumental
)

# A public fan: 124 collection items with 13 packages, 44 followed bands on 2026-09-24
TEST_PUBLIC_FAN_ID = 3477641
