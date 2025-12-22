"""Real data tests for Bandcamp API.

These tests run against the live Bandcamp API with real data.
They require BANDCAMP_IDENTITY_TOKEN environment variable to be set.

To run all real data tests:
    pytest -m manual tests/real_data/ -v

To run specific test files:
    pytest -m manual tests/real_data/test_main_api.py -v
    pytest -m manual tests/real_data/test_collection_methods.py -v
    pytest -m manual tests/real_data/test_search_and_retrieval.py -v

WARNING: These tests make real API calls and may consume rate limits.
They also require valid authentication credentials.
"""
