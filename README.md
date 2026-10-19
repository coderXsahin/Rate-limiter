# Rate Limiter API

A Python rate-limiting API built with FastAPI, implementing the **Sliding Window** and **Token Bucket** algorithms, with optional Redis-backed rate limiting for shared state across multiple application instances.

## Features

- Sliding Window rate-limiting algorithm
- Token Bucket rate-limiting algorithm
- Configurable strategy and storage backend using environment variables
- In-memory rate limiting for local development
- Redis-backed Sliding Window rate limiting
- Atomic request checks using a Redis Lua script
- Per-client and per-endpoint rate limiting
- Thread-safe request processing within an application instance
- HTTP `429 Too Many Requests` responses when limits are exceeded
- Rate-limit response headers
- Statistics endpoint for allowed and rejected requests
- Interactive API documentation with Swagger UI
- Automated tests using pytest

## Tech Stack

- Python
- FastAPI
- Uvicorn
- Redis
- Docker
- redis-py
- pytest
- HTTPX

## Getting Started

### 1. Clone the repository

```powershell
git clone https://github.com/coderXsahin/Rate-Limiter.git
cd Rate-Limiter
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Start the API with the in-memory backend

```powershell
python -m uvicorn src.main:app --reload
```

By default, the API uses the Sliding Window algorithm with in-memory storage. Redis is not required for this mode.

Open the interactive API documentation at:

http://127.0.0.1:8000/docs

## Configure the Rate-Limiting Strategy

Set `RATE_LIMIT_STRATEGY` to select the algorithm.

### Sliding Window

```powershell
$env:RATE_LIMIT_STRATEGY = "policy_a"
python -m uvicorn src.main:app --reload
```

### Token Bucket

```powershell
$env:RATE_LIMIT_STRATEGY = "policy_b"
python -m uvicorn src.main:app --reload
```

The Token Bucket strategy currently supports the in-memory backend only.

To restore the default strategy:

```powershell
Remove-Item Env:RATE_LIMIT_STRATEGY -ErrorAction SilentlyContinue
```

Stop the running server with `Ctrl+C` before restarting it with a different configuration.

## Redis Setup

Redis enables multiple application instances to share rate-limit state.

### 1. Start Redis with Docker

Make sure Docker Desktop is running, then execute:

```powershell
docker run --name rate-limiter-redis -p 6379:6379 -d redis:7-alpine
```

If the container already exists but is stopped, start it with:

```powershell
docker start rate-limiter-redis
```

### 2. Verify the Redis connection

```powershell
docker exec -it rate-limiter-redis redis-cli ping
```

Expected output:

```text
PONG
```

### 3. Enable the Redis backend

Set the backend and strategy:

```powershell
$env:RATE_LIMIT_BACKEND = "redis"
$env:RATE_LIMIT_STRATEGY = "policy_a"
```

Start the API:

```powershell
python -m uvicorn src.main:app --reload
```

The API now uses Redis to store and enforce Sliding Window rate-limit state.

To return to in-memory mode:

```powershell
Remove-Item Env:RATE_LIMIT_BACKEND -ErrorAction SilentlyContinue
Remove-Item Env:RATE_LIMIT_STRATEGY -ErrorAction SilentlyContinue
```

Then restart the API.

### Backend and strategy compatibility

| Backend | Strategy | Supported |
|---|---|---|
| `memory` | `policy_a` — Sliding Window | Yes |
| `memory` | `policy_b` — Token Bucket | Yes |
| `redis` | `policy_a` — Sliding Window | Yes |
| `redis` | `policy_b` — Token Bucket | No |

The Redis implementation uses a Lua script to perform the Sliding Window check and request recording atomically. This helps prevent concurrent application instances from independently allowing requests beyond the configured limit.

Redis connection settings can be configured with the `REDIS_URL` environment variable. The default is `redis://localhost:6379/0`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome message and active configuration |
| GET | `/health` | Health check |
| GET | `/api/resource` | Rate-limited resource |
| GET | `/api/stats` | Request statistics |
| GET | `/docs` | Interactive Swagger UI documentation |

## Rate-Limit Configuration

The default resource configuration is:

- Request limit: 5 requests
- Sliding Window duration: 60 seconds
- Token Bucket capacity: 5 tokens
- Token refill rate: 1 token per second

Rate limits are applied per client IP address and endpoint.

## Rate-Limit Headers

The `/api/resource` endpoint returns these headers:

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset-Ms`

Requests that exceed the configured limit receive HTTP `429 Too Many Requests`.

## Statistics Example

The `/api/stats` endpoint reports evaluated requests, allowed requests, rejected requests, rejection rate, and the active configuration.

Example response:

```json
{
  "total_requests": 6,
  "allowed_requests": 5,
  "rejected_requests": 1,
  "rejection_rate_percent": 16.67,
  "strategy": "policy_a",
  "backend": "redis"
}
```

Statistics are stored in application memory. They reset when the application restarts and are **not shared across multiple application instances**, even when Redis is used for rate limiting.

## Run Tests

Activate your virtual environment, ensure your local Redis container is running for the Redis integration tests, and run:

```powershell
python -m pytest -v
```

**Important:** The Redis integration tests use Redis database 0 and call `FLUSHDB`. Run them only against a dedicated development or test Redis database, never against a database containing important or production data.

## Current Limitations

- Redis currently supports the Sliding Window strategy only.
- Request statistics are stored in application memory.
- In-memory rate-limit state is not shared across application instances.
- The client identifier currently uses the request's client IP address.
- Production deployments need appropriate Redis authentication, network security, and configuration.

## Future Improvements

- Redis-backed statistics shared across instances
- Redis support for the Token Bucket strategy
- Configurable limits per endpoint and client
- More detailed monitoring and metrics
- Improved production deployment configuration
- Stronger client identification and proxy-aware IP handling
