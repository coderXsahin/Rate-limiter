
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.rate_limiter import RateLimiter


RATE_LIMIT_STRATEGY = os.getenv(
    "RATE_LIMIT_STRATEGY", "policy_a"
).strip().lower()

RATE_LIMIT_BACKEND = os.getenv(
    "RATE_LIMIT_BACKEND", "memory"
).strip().lower()

# Invalid configuration raises an error at startup.
limiter = RateLimiter(
    strategy=RATE_LIMIT_STRATEGY,
    backend=RATE_LIMIT_BACKEND,
)

app = FastAPI(
    title="Rate Limiter API",
    description=(
        "An API demonstrating configurable Sliding Window "
        "and Token Bucket rate limiting, optional Redis-backed "
        "shared rate-limit state, and request statistics."
    ),
    version="1.3.0",
)

REQUEST_LIMIT = 5
WINDOW_MS = 60_000
BUCKET_CAPACITY = 5
REFILL_RATE = 1


@app.get("/")
def home():
    return {
        "message": "Welcome to the Rate Limiter API!",
        "docs": "/docs",
        "health": "/health",
        "stats": "/api/stats",
        "strategy": limiter.strategy,
        "backend": limiter.backend,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/resource")
def get_resource(request: Request):
    client_id = (
        request.client.host
        if request.client
        else "unknown"
    )

    allowed, remaining, reset_ms = limiter.check(
        client_id=client_id,
        endpoint="/api/resource",
        limit=REQUEST_LIMIT,
        window_ms=WINDOW_MS,
        capacity=BUCKET_CAPACITY,
        refill_rate=REFILL_RATE,
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
                "message": (
                    "Too many requests. Please try again later."
                ),
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
    stats = limiter.get_stats()

    return {
        **stats,
        "strategy": limiter.strategy,
        "backend": limiter.backend,
    }
