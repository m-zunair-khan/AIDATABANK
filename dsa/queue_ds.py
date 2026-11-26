"""
Queue (FIFO - First-In, First-Out) implementation.
Project Usage: User review moderation queue. New submitted model reviews enter the queue,
and administrators process them in the exact order they were received.
Time Complexity:
  - enqueue: O(1)
  - dequeue: O(1) amortized using two stacks or collections.deque
  - peek: O(1)
  - size / is_empty: O(1)
"""
from typing import Any, List
from collections import deque


class Queue:
    """FIFO queue implementation using a double-ended queue under the hood."""
    def __init__(self):
        self._items: deque = deque()

    def enqueue(self, item: Any) -> None:
        """Add item to back of queue. O(1) time."""
        self._items.append(item)

    def dequeue(self) -> Any:
        """Remove and return item from front of queue. O(1) time. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("dequeue from empty queue")
        return self._items.popleft()

    def peek(self) -> Any:
        """Return the item at the front without removing it. O(1) time."""
        if self.is_empty():
            raise IndexError("peek from empty queue")
        return self._items[0]

    def is_empty(self) -> bool:
        """Check if queue is empty. O(1) time."""
        return len(self._items) == 0

    def size(self) -> int:
        """Return total items in queue. O(1) time."""
        return len(self._items)

    def to_list(self) -> List[Any]:
        """Convert queue to list from front to back."""
        return list(self._items)

    def clear(self) -> None:
        """Clear queue."""
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return f"Queue({list(self._items)!r})"
