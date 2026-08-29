import datetime
import string
import threading
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse


class URLRecord:
    """Represents the internal state, metadata, and analytics of a URL."""

    __slots__ = (
        "long_url",
        "short_token",
        "created_at",
        "expires_at",
        "click_count",
        "access_logs",
    )

    def __init__(
        self,
        long_url: str,
        short_token: str,
        ttl_seconds: Optional[float] = None,
    ):
        self.long_url: str = long_url
        self.short_token: str = short_token
        self.created_at: float = time.time()
        self.expires_at: Optional[float] = (
            self.created_at + ttl_seconds if ttl_seconds else None
        )
        self.click_count: int = 0
        self.access_logs: List[float] = []

    def is_expired(self) -> bool:
        """Checks if the URL has exceeded its lifespan."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def record_access(self) -> None:
        """Logs a click event atomically."""
        self.click_count += 1
        self.access_logs.append(time.time())


class AdvancedURLShortener:
    """Thread-safe URL Shortener supporting Base62 encoding, custom aliases,

    TTL expiration, URL normalization, and analytics.
    """

    # Base62 Alphabet (0-9, a-z, A-Z)
    ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
    BASE = len(ALPHABET)

    # Offset to avoid short/single-character IDs and reduce sequential predictability
    ID_OFFSET = 100_000_000

    def __init__(self, base_domain: str = "https://short.ly"):
        self.base_domain = base_domain.rstrip("/")
        self._url_db: Dict[str, URLRecord] = {}       # token -> URLRecord
        self._reverse_db: Dict[str, str] = {}         # normalized_long_url -> token
        self._counter: int = self.ID_OFFSET
        self._lock = threading.Lock()

    @classmethod
    def encode_base62(cls, num: int) -> str:
        """Converts an integer to a Base62 token."""
        if num == 0:
            return cls.ALPHABET[0]
        digits = []
        while num > 0:
            digits.append(cls.ALPHABET[num % cls.BASE])
            num //= cls.BASE
        return "".join(reversed(digits))

    @classmethod
    def decode_base62(cls, token: str) -> int:
        """Converts a Base62 token back to an integer ID."""
        num = 0
        for char in token:
            idx = cls.ALPHABET.find(char)
            if idx == -1:
                raise ValueError(f"Invalid character '{char}' in token.")
            num = num * cls.BASE + idx
        return num

    def _normalize_url(self, raw_url: str) -> str:
        """Validates and normalizes URLs to ensure consistency."""
        raw_url = raw_url.strip()
        if not raw_url.startswith(("http://", "https://")):
            raw_url = "https://" + raw_url

        parsed = urlparse(raw_url)
        if not parsed.netloc:
            raise ValueError(f"Invalid URL target: {raw_url}")

        # Lowercase scheme/host and remove redundant default ports and trailing slashes
        netloc = parsed.netloc.lower()
        if netloc.endswith(":80") and parsed.scheme == "http":
            netloc = netloc[:-3]
        elif netloc.endswith(":443") and parsed.scheme == "https":
            netloc = netloc[:-4]

        path = parsed.path.rstrip("/") if parsed.path != "/" else "/"

        normalized = urlunparse((
            parsed.scheme.lower(),
            netloc,
            path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        ))
        return normalized

    def shorten(
        self,
        long_url: str,
        custom_alias: Optional[str] = None,
        ttl_seconds: Optional[float] = None,
    ) -> str:
        """Generates or retrieves a shortened token for a URL.

        Args:
            long_url: Target URL to compress.
            custom_alias: Optional vanity alias requested by client.
            ttl_seconds: Optional time-to-live in seconds before expiration.

        Returns:
            Fully-qualified short URL.
        """
        normalized_url = self._normalize_url(long_url)

        with self._lock:
            # 1. Handle Custom Alias
            if custom_alias:
                token = custom_alias.strip()
                if token in self._url_db:
                    existing = self._url_db[token]
                    if not existing.is_expired():
                        raise ValueError(f"Alias '{token}' is already taken.")
                    # Clean up expired entry
                    del self._reverse_db[existing.long_url]

                record = URLRecord(normalized_url, token, ttl_seconds)
                self._url_db[token] = record
                self._reverse_db[normalized_url] = token
                return f"{self.base_domain}/{token}"

            # 2. Check for Existing Active Mapping
            if normalized_url in self._reverse_db:
                token = self._reverse_db[normalized_url]
                existing_record = self._url_db.get(token)
                if existing_record and not existing_record.is_expired():
                    return f"{self.base_domain}/{token}"
                # Prune expired mapping
                if existing_record:
                    del self._url_db[token]
                del self._reverse_db[normalized_url]

            # 3. Generate Sequential Base62 Token
            token = self.encode_base62(self._counter)
            self._counter += 1

            record = URLRecord(normalized_url, token, ttl_seconds)
            self._url_db[token] = record
            self._reverse_db[normalized_url] = token

            return f"{self.base_domain}/{token}"

    def retrieve(self, short_url_or_token: str) -> Optional[str]:
        """Resolves a short URL/token to its original destination and updates analytics."""
        token = short_url_or_token.split("/")[-1]

        with self._lock:
            record = self._url_db.get(token)
            if not record:
                return None

            if record.is_expired():
                # Lazy cleanup on expired access
                del self._url_db[token]
                if record.long_url in self._reverse_db:
                    del self._reverse_db[record.long_url]
                return None

            record.record_access()
            return record.long_url

    def get_analytics(self, short_url_or_token: str) -> Optional[dict]:
        """Fetches click counts, creation timestamps, and expiration status."""
        token = short_url_or_token.split("/")[-1]

        with self._lock:
            record = self._url_db.get(token)
            if not record or record.is_expired():
                return None

            return {
                "short_token": record.short_token,
                "long_url": record.long_url,
                "clicks": record.click_count,
                "created_at": datetime.datetime.fromtimestamp(
                    record.created_at, tz=datetime.timezone.utc
                ).isoformat(),
                "expires_at": (
                    datetime.datetime.fromtimestamp(
                        record.expires_at, tz=datetime.timezone.utc
                    ).isoformat()
                    if record.expires_at
                    else None
                ),
            }

    def purge_expired(self) -> int:
        """Removes all expired records from memory."""
        purged_count = 0
        with self._lock:
            tokens_to_remove = [
                token for token, rec in self._url_db.items() if rec.is_expired()
            ]
            for token in tokens_to_remove:
                rec = self._url_db.pop(token)
                self._reverse_db.pop(rec.long_url, None)
                purged_count += 1
        return purged_count
    
### Testing UrlShortener
    
    
if __name__ == "__main__":
    shortener = AdvancedURLShortener(base_domain="https://sho.rt")

    # 1. Standard Auto-Generation
    short1 = shortener.shorten("https://www.example.com/long/path/to/resource")
    print(f"Generated: {short1}")

    # 2. Custom Vanity Alias
    short2 = shortener.shorten(
        "https://github.com/openai", custom_alias="gh-openai"
    )
    print(f"Vanity:    {short2}")

    # 3. Expiration / TTL Handling
    short_temp = shortener.shorten(
        "https://news.ycombinator.com", ttl_seconds=1.0
    )
    print(f"Temporary: {short_temp}")

    # 4. Retrieval & Analytics Tracking
    print("Resolved:", shortener.retrieve(short2))
    print("Resolved:", shortener.retrieve(short2))
    print("Analytics:", shortener.get_analytics(short2))

    # 5. Check Expiration
    time.sleep(1.1)
    print("Expired Lookup (should be None):", shortener.retrieve(short_temp))