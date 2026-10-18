
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

        # Statistics counters
        self.total_requests = 0
        self.allowed_requests = 0
        self.rejected_requests = 0

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
                result = self._sliding_window(
                    client_id, endpoint, limit, window_ms
                )
            else:
                result = self._token_bucket(
                    client_id, endpoint, capacity, refill_rate
                )

            allowed, remaining, reset_ms = result

            # Record the outcome of every evaluated request.
            self.total_requests += 1

            if allowed:
                self.allowed_requests += 1
            else:
                self.rejected_requests += 1

            return allowed, remaining, reset_ms

    def get_stats(self):
        with self.lock:
            if self.total_requests == 0:
                rejection_rate = 0.0
            else:
                rejection_rate = (
                    self.rejected_requests
                    / self.total_requests
                    * 100
                )

            return {
                "total_requests": self.total_requests,
                "allowed_requests": self.allowed_requests,
                "rejected_requests": self.rejected_requests,
                "rejection_rate_percent": round(rejection_rate, 2),
            }

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
