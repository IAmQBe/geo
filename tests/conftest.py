import pytest


@pytest.fixture
def sample_parsed_payload() -> dict:
    return {
        "name": "Test Cafe",
        "address": "Main street 1",
        "source_url": "https://example.com/place/1",
        "source_id": "src-1",
        "rating": 4.5,
        "review_count": 10,
    }
