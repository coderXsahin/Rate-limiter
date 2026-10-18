
from fastapi.testclient import TestClient

from src.main import app, limiter

client = TestClient(app)


def setup_function():
    # Reset the limiter before each test.
    limiter.requests.clear()
    limiter.buckets.clear()


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
