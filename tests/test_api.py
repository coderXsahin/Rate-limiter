
from fastapi.testclient import TestClient

from src.main import app, limiter

client = TestClient(app)


def setup_function():
    # Reset limiter state and statistics before each test.
    with limiter.lock:
        limiter.requests.clear()
        limiter.buckets.clear()

        limiter.total_requests = 0
        limiter.allowed_requests = 0
        limiter.rejected_requests = 0


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to the Rate Limiter API!"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_resource_allows_requests_within_limit():
    response = client.get("/api/resource")

    assert response.status_code == 200
    assert response.json()["message"] == "Request allowed!"
    assert response.headers["X-RateLimit-Limit"] == "5"
    assert response.headers["X-RateLimit-Remaining"] == "4"


def test_resource_rejects_sixth_request():
    responses = [
        client.get("/api/resource")
        for _ in range(6)
    ]

    assert all(response.status_code == 200 for response in responses[:5])
    assert responses[5].status_code == 429
    assert responses[5].json()["error"] == "Rate limit exceeded"


def test_rate_limit_headers_are_returned():
    response = client.get("/api/resource")

    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset-Ms" in response.headers



def test_stats_are_zero_initially():
    response = client.get("/api/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total_requests": 0,
        "allowed_requests": 0,
        "rejected_requests": 0,
        "rejection_rate_percent": 0.0,
        "strategy": limiter.strategy,
        "backend": limiter.backend,
    }




def test_stats_track_allowed_and_rejected_requests():
    # The first five requests should be allowed.
    for _ in range(5):
        response = client.get("/api/resource")
        assert response.status_code == 200

    # The sixth request should be rejected.
    response = client.get("/api/resource")
    assert response.status_code == 429

    # Statistics requests are not counted in the totals.
    response = client.get("/api/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total_requests": 6,
        "allowed_requests": 5,
        "rejected_requests": 1,
        "rejection_rate_percent": 16.67,
        "strategy": limiter.strategy,
        "backend": limiter.backend,
    }

