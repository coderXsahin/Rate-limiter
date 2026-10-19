
from src.redis_client import redis_client


def test_redis_connection():
    assert redis_client.ping() is True

from src.redis_client import check_redis_sliding_window


def test_redis_sliding_window_allows_requests_within_limit():
    client = redis_client
    client_id = "test-client-allowed"
    endpoint = "/test-resource"

    client.flushdb()

    for expected_remaining in range(4, -1, -1):
        allowed, remaining, reset_ms = check_redis_sliding_window(
            client, client_id, endpoint, 5, 60_000
        )

        assert allowed is True
        assert remaining == expected_remaining
        assert reset_ms >= 0


def test_redis_sliding_window_rejects_request_over_limit():
    client = redis_client
    client_id = "test-client-rejected"
    endpoint = "/test-resource"

    client.flushdb()

    for _ in range(5):
        allowed, _, _ = check_redis_sliding_window(
            client, client_id, endpoint, 5, 60_000
        )
        assert allowed is True

    allowed, remaining, reset_ms = check_redis_sliding_window(
        client, client_id, endpoint, 5, 60_000
    )

    assert allowed is False
    assert remaining == 0
    assert reset_ms > 0


def test_redis_sliding_window_isolates_clients():
    client = redis_client
    client.flushdb()

    for _ in range(5):
        check_redis_sliding_window(
            client, "client-A", "/resource", 5, 60_000
        )

    allowed, remaining, _ = check_redis_sliding_window(
        client, "client-B", "/resource", 5, 60_000
    )

    assert allowed is True
    assert remaining == 4
