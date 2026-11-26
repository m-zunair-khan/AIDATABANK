"""
Circular Queue (Ring Buffer) implementation.
Project Usage: "Recently Viewed Models" buffer. Fixed-size buffer (default 10 items)
that overwrites the oldest items when full, always maintaining the most recent history.
Time Complexity:
  - enqueue: O(1)
  - dequeue: O(1)
  - peek: O(1)
  - to_list: O(k) where k is current count
"""
from typing import Any, List, Optional


class CircularQueue:
    """Fixed-capacity ring buffer with overwrite semantics on full enqueue."""
    def __init__(self, capacity: int = 10):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity: int = capacity
        self._buffer: List[Optional[Any]] = [None] * capacity
        self._front: int = 0
        self._rear: int = 0
        self._count: int = 0

    def enqueue(self, item: Any) -> None:
        """
        Add item to circular queue.
        If queue is full, overwrite the oldest item at front and advance front.
        O(1) time.
        """
        if self.is_full():
            # Overwrite oldest item at front
            self._buffer[self._rear] = item
            self._front = (self._front + 1) % self.capacity
            self._rear = (self._rear + 1) % self.capacity
        else:
            self._buffer[self._rear] = item
            self._rear = (self._rear + 1) % self.capacity
            self._count += 1

    def dequeue(self) -> Any:
        """Remove and return front item. O(1) time. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("dequeue from empty circular queue")
        item = self._buffer[self._front]
        self._buffer[self._front] = None
        self._front = (self._front + 1) % self.capacity
        self._count -= 1
        return item

    def peek(self) -> Any:
        """View front item without removing. O(1) time."""
        if self.is_empty():
            raise IndexError("peek from empty circular queue")
        return self._buffer[self._front]

    def is_full(self) -> bool:
        """Check if queue is full."""
        return self._count == self.capacity

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self._count == 0

    def to_list(self) -> List[Any]:
        """Return list of items ordered from oldest to newest. O(k) time."""
        result = []
        for i in range(self._count):
            idx = (self._front + i) % self.capacity
            result.append(self._buffer[idx])
        return result

    def clear(self) -> None:
        self._buffer = [None] * self.capacity
        self._front = 0
        self._rear = 0
        self._count = 0

    def __len__(self) -> int:
        return self._count

    def __repr__(self) -> str:
        return f"CircularQueue(capacity={self.capacity}, items={self.to_list()!r})"
