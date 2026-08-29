from collections import deque
import threading
import time
from typing import Dict, NamedTuple, Optional, Tuple


class RateLimitResult(NamedTuple):
    """Encapsulates the decision and metadata for an evaluated request."""

    allowed: bool
    remaining: int
    reset_after: float
    retry_after: Optional[float]


class SlidingWindowRateLimiter:
    """Thread-safe, sliding-window log rate limiter with automated memory cleanup.

    Tracks timestamps of incoming requests within a rolling time window to provide
    accurate, boundary-smooth rate limiting without fixed-window edge bursts.

    Attributes:
        default_max_requests (int): Fallback capacity if no custom limit is set.
        default_window_seconds (float): Fallback time window in seconds.
    """

    def __init__(
        self,
        default_max_requests: int,
        default_window_seconds: float,
        cleanup_interval_seconds: float = 60.0,
    ) -> None:
        """Initializes the rate limiter and starts the background eviction daemon.

        Args:
            default_max_requests: Maximum allowed hits per default window.
            default_window_seconds: Window duration in seconds.
            cleanup_interval_seconds: Frequency of background memory cleanup sweeps.
        """
        self.default_max = int(default_max_requests)
        self.default_window = float(default_window_seconds)
        self.cleanup_interval = float(cleanup_interval_seconds)

        # Storage mapping: key -> deque of monotonic timestamps
        self._store: Dict[str, deque] = {}

        # Custom configured limits: key -> (max_requests, window_seconds)
        self._limits: Dict[str, Tuple[int, float]] = {}

        # Granular per-key locks to prevent global thread contention
        self._locks: Dict[str, threading.Lock] = {}

        # Master lock guarding internal dictionary mutations (adding/removing keys)
        self._master_lock = threading.Lock()

        # Background cleanup thread to prevent unbounded memory growth
        self._shutdown_event = threading.Event()
        self._cleanup_thread = threading.Thread(
            target=self._background_cleanup, daemon=True
        )
        self._cleanup_thread.start()

    def _get_key_lock(self, key: str) -> threading.Lock:
        """Retrieves or creates a thread-safe Lock instance for a given key.

        Guarantees that two concurrent requests for an uninitialized key
        receive the exact same Lock instance.
        """
        with self._master_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

    def set_limit(
        self, key: str, max_requests: int, window_seconds: float
    ) -> None:
        """Overrides the rate limit configuration for a specific key.

        Args:
            key: Target identifier (e.g., client IP, user ID, API token).
            max_requests: Request quota for the key.
            window_seconds: Duration of the rolling window in seconds.
        """
        with self._master_lock:
            self._limits[key] = (int(max_requests), float(window_seconds))

    def get_limit(self, key: str) -> Tuple[int, float]:
        """Fetches the limit configuration for a key, falling back to defaults."""
        with self._master_lock:
            return self._limits.get(key, (self.default_max, self.default_window))

    def allow_request(self, key: str) -> RateLimitResult:
        """Evaluates whether an incoming request is permitted under the sliding window.

        Args:
            key: Target identifier making the request.

        Returns:
            RateLimitResult: NamedTuple containing:
                - allowed (bool): True if request can proceed, False if limited.
                - remaining (int): Quota slots left within the active window.
                - reset_after (float): Seconds until the entire window resets.
                - retry_after (Optional[float]): Seconds until the oldest request expires (None if allowed).
        """
        now = time.monotonic()
        max_requests, window_seconds = self.get_limit(key)
        lock = self._get_key_lock(key)

        with lock:
            if key not in self._store:
                self._store[key] = deque()
            q = self._store[key]

            # Evict timestamps that fall outside the current rolling window
            boundary = now - window_seconds
            while q and q[0] <= boundary:
                q.popleft()

            if len(q) < max_requests:
                q.append(now)
                remaining = max_requests - len(q)
                # Reset time is relative to the oldest entry in the active window
                reset_after = max(0.0, (q[0] + window_seconds) - now)
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining,
                    reset_after=reset_after,
                    retry_after=None,
                )
            else:
                # Quota exceeded: calculate wait time based on when the oldest request drops out
                oldest = q[0]
                retry_after = max(0.0, (oldest + window_seconds) - now)
                reset_after = retry_after
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_after=reset_after,
                    retry_after=retry_after,
                )

    def get_usage(self, key: str) -> Tuple[int, int, float]:
        """Inspects the current state of a key without consuming quota.

        Args:
            key: Target identifier.

        Returns:
            Tuple[int, int, float]: (current_usage_count, max_limit, time_to_earliest_slot_recovery)
        """
        now = time.monotonic()
        max_requests, window_seconds = self.get_limit(key)
        lock = self._get_key_lock(key)

        with lock:
            if key not in self._store:
                return (0, max_requests, 0.0)

            q = self._store[key]
            boundary = now - window_seconds

            # Prune expired timestamps inside the lock boundary
            while q and q[0] <= boundary:
                q.popleft()

            count = len(q)
            if count == 0:
                return (0, max_requests, 0.0)

            ttl = max(0.0, (q[0] + window_seconds) - now)
            return (count, max_requests, ttl)

    def _background_cleanup(self) -> None:
        """Background thread worker that removes idle keys to prevent memory leaks."""
        while not self._shutdown_event.wait(self.cleanup_interval):
            now = time.monotonic()
            with self._master_lock:
                all_keys = list(self._store.keys())

            for key in all_keys:
                _, window_seconds = self.get_limit(key)
                lock = self._get_key_lock(key)
                with lock:
                    if key in self._store:
                        q = self._store[key]
                        boundary = now - window_seconds
                        while q and q[0] <= boundary:
                            q.popleft()

                        # If no requests exist within the window, delete key and lock references
                        if not q:
                            del self._store[key]
                            with self._master_lock:
                                self._locks.pop(key, None)

    def close(self) -> None:
        """Stops the background eviction thread."""
        self._shutdown_event.set()
        self._cleanup_thread.join()
        
        
# Testing RateLimiter
        
        
if __name__ == "__main__":
    # Create a limiter: default 5 requests per 2.0-second window
    limiter = SlidingWindowRateLimiter(
        default_max_requests=5,
        default_window_seconds=2.0,
        cleanup_interval_seconds=5.0,
    )

    # Set custom quota for a VIP user
    limiter.set_limit("vip_user_1", max_requests=10, window_seconds=2.0)

    # Test standard client hits
    client = "192.168.1.50"
    for i in range(1, 8):
        res = limiter.allow_request(client)
        if res.allowed:
            print(f"Request {i}: ALLOWED (Remaining: {res.remaining})")
        else:
            print(
                f"Request {i}: BLOCKED (Retry-After: {res.retry_after:.3f}s)"
            )
        time.sleep(0.1)

    # Inspect usage
    usage, limit, ttl = limiter.get_usage(client)
    print(f"\nUsage for {client}: {usage}/{limit} slots used. Next slot frees in {ttl:.3f}s")

    # Clean shutdown
    limiter.close()