
import time
import threading
from collections import deque


class RateLimiter:
    def __init__(self, strategy="policy_a"):
        if strategy not in ("policy_a", "policy_b"):
            raise ValueError(f"Unknown strategy: {strategy}")

        self.strategy = strategy
        self.requests = {}
        self.buckets = {}
        self.lock = threading.Lock()

    def check(
        self,
        client_id,
        endpoint,
        limit,
        window_ms,
        capacity,
        refill_rate,
    ):
        with self.lock:
            if self.strategy == "policy_a":
                return self._sliding_window(
                    client_id, endpoint, limit, window_ms
                )

            return self._token_bucket(
                client_id, endpoint, capacity, refill_rate
            )

    # Policy A: Sliding Window
    def _sliding_window(self, client_id, endpoint, limit, window_ms):
        key = (client_id, endpoint)
        now = time.monotonic()
        window_seconds = window_ms / 1000.0

        if key not in self.requests:
            self.requests[key] = deque()

        timestamps = self.requests[key]

        while timestamps and timestamps[0] + window_seconds <= now:
            timestamps.popleft()

        if limit <= 0:
            return False, 0, 0

        if len(timestamps) >= limit:
            reset_ms = max(
                0, int((timestamps[0] + window_seconds - now) * 1000)
            )
            return False, 0, reset_ms

        timestamps.append(now)
        remaining = limit - len(timestamps)

        reset_ms = max(
            0, int((timestamps[0] + window_seconds - now) * 1000)
        )

        return True, remaining, reset_ms

    # Policy B: Token Bucket
    def _token_bucket(self, client_id, endpoint, capacity, refill_rate):
        key = (client_id, endpoint)
        now = time.monotonic()

        if key not in self.buckets:
            self.buckets[key] = {
                "tokens": float(max(0, capacity)),
                "last_time": now,
            }

        bucket = self.buckets[key]

        elapsed = now - bucket["last_time"]

        if elapsed > 0 and refill_rate > 0:
            bucket["tokens"] = min(
                float(max(0, capacity)),
                bucket["tokens"] + elapsed * refill_rate,
            )

        bucket["last_time"] = now

        if capacity <= 0:
            return False, 0, 0

        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            remaining = int(bucket["tokens"])
            return True, remaining, 0

        if refill_rate <= 0:
            return False, 0, 0

        tokens_needed = 1.0 - bucket["tokens"]
        reset_ms = max(0, int(tokens_needed / refill_rate * 1000))

        return False, 0, reset_ms
