
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.rate_limiter import RateLimiter

app = FastAPI(
    title="Rate Limiter API",
    description=(
        "An API demonstrating Sliding Window and Token Bucket "
        "rate limiting, with request statistics."
    ),
    version="1.1.0",
)

# Create one shared limiter for the application.
limiter = RateLimiter(strategy="policy_a")

# Configuration for the Sliding Window strategy.
REQUEST_LIMIT = 5
WINDOW_MS = 60_000


@app.get("/")
def home():
    return {
        "message": "Welcome to the Rate Limiter API!",
        "docs": "/docs",
        "health": "/health",
        "stats": "/api/stats",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/resource")
def get_resource(request: Request):
    # Use the caller's IP address as the client identifier.
    client_id = request.client.host if request.client else "unknown"

    allowed, remaining, reset_ms = limiter.check(
        client_id,
        "/api/resource",
        REQUEST_LIMIT,
        WINDOW_MS,
        5,
        1,
    )

    headers = {
        "X-RateLimit-Limit": str(REQUEST_LIMIT),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset-Ms": str(reset_ms),
    }

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "remaining": remaining,
                "reset_ms": reset_ms,
            },
            headers=headers,
        )

    return JSONResponse(
        status_code=200,
        content={
            "message": "Request allowed!",
            "remaining": remaining,
        },
        headers=headers,
    )


@app.get("/api/stats")
def get_statistics():
    # Reading statistics does not count as a rate-limited request.
    return limiter.get_stats()
