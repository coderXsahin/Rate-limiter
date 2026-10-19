
import os
import time
import uuid
import hashlib

import redis


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)


def create_redis_client():
    """Create a Redis client using the configured Redis URL."""
    return redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )


redis_client = create_redis_client()


SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local member = ARGV[3]

local server_time = redis.call('TIME')
local now_ms = tonumber(server_time[1]) * 1000
    + math.floor(tonumber(server_time[2]) / 1000)

local window_start = now_ms - window_ms

redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)

local count = redis.call('ZCARD', key)

if limit <= 0 then
    return {0, 0, 0}
end

if count >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local reset_ms = 0

    if #oldest > 0 then
        reset_ms = math.max(
            0,
            tonumber(oldest[2]) + window_ms - now_ms
        )
    end

    return {0, 0, reset_ms}
end

redis.call('ZADD', key, now_ms, member)
redis.call('PEXPIRE', key, window_ms)

count = count + 1

local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
local reset_ms = 0

if #oldest > 0 then
    reset_ms = math.max(
        0,
        tonumber(oldest[2]) + window_ms - now_ms
    )
end

return {1, limit - count, reset_ms}
"""


def check_redis_sliding_window(
    client,
    client_id,
    endpoint,
    limit,
    window_ms,
):
    """Atomically check and record a request using Redis."""
    identity = f"{client_id}:{endpoint}"
    key_hash = hashlib.sha256(identity.encode()).hexdigest()
    redis_key = f"rate_limiter:sliding:{key_hash}"

    unique_member = f"{time.time_ns()}:{uuid.uuid4().hex}"

    result = client.eval(
        SLIDING_WINDOW_SCRIPT,
        1,
        redis_key,
        limit,
        window_ms,
        unique_member,
    )

    allowed, remaining, reset_ms = result

    return bool(allowed), int(remaining), int(reset_ms)
