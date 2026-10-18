
from src.rate_limiter import RateLimiter


def test_accepts_requests_within_limit():
    limiter = RateLimiter()

    first = limiter.check("alice", "/api/chat", 2, 10_000, 2, 1)
    second = limiter.check("alice", "/api/chat", 2, 10_000, 2, 1)

    assert first[0] is True
    assert first[1] == 1
    assert second[0] is True
    assert second[1] == 0


def test_rejects_request_over_limit():
    limiter = RateLimiter()

    limiter.check("alice", "/api/chat", 2, 10_000, 2, 1)
    limiter.check("alice", "/api/chat", 2, 10_000, 2, 1)

    third = limiter.check("alice", "/api/chat", 2, 10_000, 2, 1)

    assert third[0] is False
    assert third[1] == 0
    assert third[2] >= 0


def test_clients_have_separate_limits():
    limiter = RateLimiter()

    limiter.check("alice", "/api/chat", 1, 10_000, 1, 1)

    bob_request = limiter.check("bob", "/api/chat", 1, 10_000, 1, 1)

    assert bob_request[0] is True


def test_endpoints_have_separate_limits():
    limiter = RateLimiter()

    limiter.check("alice", "/api/chat", 1, 10_000, 1, 1)

    orders_request = limiter.check(
        "alice", "/api/orders", 1, 10_000, 1, 1
    )

    assert orders_request[0] is True


def test_token_bucket_initial_capacity():
    limiter = RateLimiter(strategy="policy_b")

    first = limiter.check("alice", "/api/chat", 10, 10_000, 3, 0.5)
    second = limiter.check("alice", "/api/chat", 10, 10_000, 3, 0.5)
    third = limiter.check("alice", "/api/chat", 10, 10_000, 3, 0.5)
    fourth = limiter.check("alice", "/api/chat", 10, 10_000, 3, 0.5)

    assert first == (True, 2, 0)
    assert second == (True, 1, 0)
    assert third == (True, 0, 0)
    assert fourth[0] is False
    assert fourth[1] == 0
    assert fourth[2] >= 0


def test_token_bucket_isolates_clients():
    limiter = RateLimiter(strategy="policy_b")

    limiter.check("alice", "/api/chat", 10, 10_000, 1, 0.5)

    alice_second = limiter.check(
        "alice", "/api/chat", 10, 10_000, 1, 0.5
    )
    bob_first = limiter.check(
        "bob", "/api/chat", 10, 10_000, 1, 0.5
    )

    assert alice_second[0] is False
    assert bob_first == (True, 0, 0)


def test_sliding_window_strategy_configuration():
    limiter = RateLimiter(strategy="policy_a")

    assert limiter.strategy == "policy_a"


def test_token_bucket_strategy_configuration():
    limiter = RateLimiter(strategy="policy_b")

    assert limiter.strategy == "policy_b"


def test_invalid_strategy_is_rejected():
    import pytest

    with pytest.raises(ValueError, match="Unknown strategy"):
        RateLimiter(strategy="policy_c")
