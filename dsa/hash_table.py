"""
Hash Table with Separate Chaining and TTL-based expiration.
Project Usage: In-memory query result caching to avoid repeated database hits.
Time Complexity:
  - put: O(1) average, O(n) worst-case collision
  - get: O(1) average, O(n) worst-case
  - delete: O(1) average
"""
import time
from typing import Any, List, Optional, Tuple


class HashEntry:
    """Entry storing key, value, and expiration timestamp."""
    def __init__(self, key: str, value: Any, ttl: Optional[float] = None):
        self.key = key
        self.value = value
        self.expires_at = (time.time() + ttl) if ttl is not None else None

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class HashTable:
    """Hash Table using separate chaining for collision resolution and TTL caching."""
    def __init__(self, capacity: int = 64):
        self.capacity = max(16, capacity)
        self._buckets: List[List[HashEntry]] = [[] for _ in range(self.capacity)]
        self._size = 0

    def _hash(self, key: str) -> int:
        """Hash function using polynomial rolling hash."""
        h = 0
        for ch in key:
            h = (h * 31 + ord(ch)) % self.capacity
        return h

    def put(self, key: str, value: Any, ttl: Optional[float] = 300.0) -> None:
        """Store key-value pair with optional TTL in seconds. O(1) average time."""
        idx = self._hash(key)
        bucket = self._buckets[idx]

        for entry in bucket:
            if entry.key == key:
                entry.value = value
                entry.expires_at = (time.time() + ttl) if ttl is not None else None
                return

        bucket.append(HashEntry(key, value, ttl))
        self._size += 1

        # Resize if load factor > 0.75
        if self._size / self.capacity > 0.75:
            self._resize(self.capacity * 2)

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value by key if not expired. O(1) average time."""
        idx = self._hash(key)
        bucket = self._buckets[idx]
        for i, entry in enumerate(bucket):
            if entry.key == key:
                if entry.is_expired():
                    bucket.pop(i)
                    self._size -= 1
                    return None
                return entry.value
        return None

    def delete(self, key: str) -> bool:
        """Remove entry by key. O(1) average time."""
        idx = self._hash(key)
        bucket = self._buckets[idx]
        for i, entry in enumerate(bucket):
            if entry.key == key:
                bucket.pop(i)
                self._size -= 1
                return True
        return False

    def contains(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self) -> None:
        self._buckets = [[] for _ in range(self.capacity)]
        self._size = 0

    def keys(self) -> List[str]:
        """Return list of valid unexpired keys."""
        valid_keys = []
        for bucket in self._buckets:
            for entry in bucket:
                if not entry.is_expired():
                    valid_keys.append(entry.key)
        return valid_keys

    def size(self) -> int:
        """Count active unexpired items."""
        count = 0
        for bucket in self._buckets:
            for entry in bucket:
                if not entry.is_expired():
                    count += 1
        return count

    def _resize(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self.capacity = new_capacity
        self._buckets = [[] for _ in range(new_capacity)]
        self._size = 0

        for bucket in old_buckets:
            for entry in bucket:
                if not entry.is_expired():
                    idx = self._hash(entry.key)
                    self._buckets[idx].append(entry)
                    self._size += 1

    def __len__(self) -> int:
        return self.size()

    def __repr__(self) -> str:
        return f"HashTable(capacity={self.capacity}, active_entries={self.size()})"
