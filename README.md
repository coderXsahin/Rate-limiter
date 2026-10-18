
# Rate Limiter API

A Python rate-limiting API built with FastAPI, implementing the Sliding Window and Token Bucket algorithms.

## Features

- Sliding Window rate-limiting algorithm
- Token Bucket rate-limiting algorithm
- Configurable algorithm selection using an environment variable
- Per-client and per-endpoint rate limiting
- Thread-safe request processing
- HTTP 429 responses when the limit is exceeded
- Rate-limit response headers
- Statistics endpoint for allowed and rejected requests
- Interactive API documentation with Swagger UI
- Automated tests using pytest

## Tech Stack

- Python
- FastAPI
- Uvicorn
- pytest
- HTTPX

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/coderXsahin/Rate-Limiter.git
cd Rate-Limiter
```

Replace `coderXsahin` with your GitHub username.

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Start the API

```powershell
python -m uvicorn src.main:app --reload
```

By default, the API uses the Sliding Window algorithm.

## Configure the Algorithm

The active algorithm is selected using the `RATE_LIMIT_STRATEGY` environment variable.

### Sliding Window

Windows PowerShell:

```powershell
$env:RATE_LIMIT_STRATEGY = "policy_a"
python -m uvicorn src.main:app --reload
```

### Token Bucket

Windows PowerShell:

```powershell
$env:RATE_LIMIT_STRATEGY = "policy_b"
python -m uvicorn src.main:app --reload
```

To return to the default configuration:

```powershell
Remove-Item Env:RATE_LIMIT_STRATEGY -ErrorAction SilentlyContinue
python -m uvicorn src.main:app --reload
```

The selected strategy is available from the home endpoint and statistics endpoint.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API welcome message and active strategy |
| GET | `/health` | Health check |
| GET | `/api/resource` | Rate-limited resource |
| GET | `/api/stats` | Request statistics |
| GET | `/docs` | Interactive Swagger documentation |

## Rate-Limit Configuration

The default resource configuration is:

- Request limit: 5 requests
- Sliding Window duration: 60 seconds
- Token Bucket capacity: 5 tokens
- Token refill rate: 1 token per second

## Rate-Limit Headers

The resource endpoint returns:

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset-Ms`

Requests exceeding the configured limit receive HTTP `429 Too Many Requests`.

## Statistics Example

The `/api/stats` endpoint returns the number of evaluated, allowed, and rejected requests, along with the rejection rate and active strategy.

```json
{
  "total_requests": 6,
  "allowed_requests": 5,
  "rejected_requests": 1,
  "rejection_rate_percent": 16.67,
  "strategy": "policy_a"
}
```

Statistics are stored in memory and reset when the application restarts.

## Run Tests

```powershell
python -m pytest -v
```

## Current Limitations

- Statistics and rate-limit state are stored in application memory.
- Multiple application instances do not share rate-limit state.
- The current client identifier uses the request's client IP address.

## Future Improvements

- Redis-backed shared rate limiting
- More detailed monitoring and metrics
- Configurable limits per endpoint
- Improved production deployment configuration
