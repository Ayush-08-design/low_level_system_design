import threading
import time
from typing import Optional


class InvalidSystemClock(Exception):
    """Raised when the system clock moves backwards."""
    pass


class ProductionSnowflakeGenerator:
    """
    Thread-safe, 64-bit Twitter Snowflake ID Generator.

    Bit Allocation:
    - 1  bit  : Sign bit (always 0 for positive 64-bit integer)
    - 41 bits : Milliseconds since custom epoch (lasts ~69 years)
    - 5  bits : Datacenter ID (0 - 31)
    - 5  bits : Worker/Machine ID (0 - 31)
    - 12 bits : Sequence counter (0 - 4095 per millisecond)
    """

    # Bit lengths
    SEQUENCE_BITS = 12
    WORKER_ID_BITS = 5
    DATACENTER_ID_BITS = 5

    # Maximum bounds
    MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1        # 31
    MAX_DATACENTER_ID = (1 << DATACENTER_ID_BITS) - 1  # 31
    MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1          # 4095

    # Bit shift positions
    WORKER_ID_SHIFT = SEQUENCE_BITS
    DATACENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS
    TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS

    # Custom Epoch (e.g., 2024-01-01 00:00:00 UTC in ms)
    # Extends 41-bit timestamp longevity to ~2093
    DEFAULT_EPOCH = 1704067200000

    def __init__(
        self,
        worker_id: int = 1,
        datacenter_id: int = 1,
        epoch: int = DEFAULT_EPOCH,
        max_backward_ms: int = 5
    ):
        if not (0 <= worker_id <= self.MAX_WORKER_ID):
            raise ValueError(f"Worker ID must be between 0 and {self.MAX_WORKER_ID}")
        if not (0 <= datacenter_id <= self.MAX_DATACENTER_ID):
            raise ValueError(f"Datacenter ID must be between 0 and {self.MAX_DATACENTER_ID}")

        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.epoch = epoch
        self.max_backward_ms = max_backward_ms

        self.sequence = 0
        self.last_timestamp = -1
        self._lock = threading.Lock()

    def _current_millis(self) -> int:
        """Returns the current monotonic wall clock time in milliseconds."""
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_ts: int) -> int:
        """Yields execution via sleep to prevent high CPU utilization during busy-wait."""
        ts = self._current_millis()
        while ts <= last_ts:
            time.sleep(0.0001)  # 100 microseconds sleep
            ts = self._current_millis()
        return ts

    def get_id(self) -> int:
        """Generates a globally unique, k-sorted, 64-bit integer ID."""
        with self._lock:
            ts = self._current_millis()

            # Handle clock backwards anomalies
            if ts < self.last_timestamp:
                drift = self.last_timestamp - ts
                if drift <= self.max_backward_ms:
                    # Tolerable minor drift: wait out the clock skew
                    ts = self._wait_next_millis(self.last_timestamp)
                else:
                    raise InvalidSystemClock(
                        f"Clock moved backwards by {drift}ms. Refusing to generate ID."
                    )

            # Sequence generation within the same millisecond
            if ts == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
                if self.sequence == 0:
                    # Sequence overflow (exceeded 4096 IDs in 1ms)
                    ts = self._wait_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = ts

            # Compose 64-bit integer
            unique_id = (
                ((ts - self.epoch) << self.TIMESTAMP_SHIFT)
                | (self.datacenter_id << self.DATACENTER_ID_SHIFT)
                | (self.worker_id << self.WORKER_ID_SHIFT)
                | self.sequence
            )
            return unique_id


# ---------------------------------------------------------------------------
# Demonstration & Parsing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    generator = ProductionSnowflakeGenerator(worker_id=2, datacenter_id=1)
    new_id = generator.get_id()
    print(f"Generated Snowflake ID: {new_id} (Bit length: {new_id.bit_length()})")

    # Helper function to inspect generated components
    def inspect_id(snowflake_id: int, epoch: int = ProductionSnowflakeGenerator.DEFAULT_EPOCH):
        seq = snowflake_id & 0xFFF
        worker = (snowflake_id >> 12) & 0x1F
        dc = (snowflake_id >> 17) & 0x1F
        ts = (snowflake_id >> 22) + epoch
        return {
            "timestamp_ms": ts,
            "utc_datetime": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts / 1000)),
            "datacenter_id": dc,
            "worker_id": worker,
            "sequence": seq,
        }

    print("Decoded Metadata:", inspect_id(new_id))