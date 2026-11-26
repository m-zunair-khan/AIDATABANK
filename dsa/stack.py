"""
Stack (LIFO - Last-In, First-Out) implementation.
Project Usage: Filter undo system. When a user applies search filters (price, context, tags),
each filter state is pushed to the stack. Users can undo to pop the previous filter state.
Time Complexity:
  - push: O(1)
  - pop: O(1)
  - peek: O(1)
  - size / is_empty: O(1)
"""
from typing import Any, List


class Stack:
    """Stack implementation for managing filter states and undo history."""
    def __init__(self):
        self._items: List[Any] = []

    def push(self, item: Any) -> None:
        """Push item onto the top of the stack. O(1) time."""
        self._items.append(item)

    def pop(self) -> Any:
        """Pop item from top of stack. O(1) time. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> Any:
        """Return the top item without removing it. O(1) time."""
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self._items[-1]

    def is_empty(self) -> bool:
        """Check if stack is empty. O(1) time."""
        return len(self._items) == 0

    def size(self) -> int:
        """Return count of items. O(1) time."""
        return len(self._items)

    def to_list(self) -> List[Any]:
        """Return list representation from top to bottom."""
        return list(reversed(self._items))

    def clear(self) -> None:
        """Clear all items."""
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return f"Stack({self._items!r})"
