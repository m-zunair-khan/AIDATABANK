"""
Doubly Linked List implementation.
Project Usage: Model browsing history with forward/backward navigation.
Time Complexity:
  - append: O(1)
  - prepend: O(1)
  - move_forward: O(1)
  - move_backward: O(1)
  - current: O(1)
  - delete: O(n)
"""
from typing import Any, List, Optional


class DNode:
    """A node in a doubly linked list."""
    def __init__(self, data: Any, prev_node: Optional['DNode'] = None, next_node: Optional['DNode'] = None):
        self.data = data
        self.prev = prev_node
        self.next = next_node

    def __repr__(self) -> str:
        return f"DNode({self.data!r})"


class DoublyLinkedList:
    """
    Doubly linked list with a navigational cursor.
    Allows users to navigate their model viewing history (back and forward).
    """
    def __init__(self):
        self.head: Optional[DNode] = None
        self.tail: Optional[DNode] = None
        self.cursor: Optional[DNode] = None
        self._size: int = 0

    def append(self, data: Any) -> None:
        """Append data to the end and point cursor to the newly added item. O(1) time."""
        new_node = DNode(data, prev_node=self.tail, next_node=None)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            assert self.tail is not None
            self.tail.next = new_node
            self.tail = new_node
        self.cursor = new_node
        self._size += 1

    def prepend(self, data: Any) -> None:
        """Prepend data to the front. O(1) time."""
        new_node = DNode(data, prev_node=None, next_node=self.head)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
            self.cursor = new_node
        else:
            self.head.prev = new_node
            self.head = new_node
        self._size += 1

    def move_forward(self) -> Optional[Any]:
        """Move cursor forward by one node. Returns data at new cursor or None."""
        if self.cursor and self.cursor.next:
            self.cursor = self.cursor.next
            return self.cursor.data
        return None

    def move_backward(self) -> Optional[Any]:
        """Move cursor backward by one node. Returns data at new cursor or None."""
        if self.cursor and self.cursor.prev:
            self.cursor = self.cursor.prev
            return self.cursor.data
        return None

    def current(self) -> Optional[Any]:
        """Get the current cursor data. O(1) time."""
        return self.cursor.data if self.cursor else None

    def delete(self, data: Any) -> bool:
        """Delete the first occurrence of data. O(n) time."""
        curr = self.head
        while curr is not None:
            if curr.data == data:
                if curr == self.cursor:
                    self.cursor = curr.next or curr.prev
                if curr.prev:
                    curr.prev.next = curr.next
                else:
                    self.head = curr.next

                if curr.next:
                    curr.next.prev = curr.prev
                else:
                    self.tail = curr.prev

                self._size -= 1
                return True
            curr = curr.next
        return False

    def to_list(self) -> List[Any]:
        """Convert list to Python array."""
        result = []
        curr = self.head
        while curr is not None:
            result.append(curr.data)
            curr = curr.next
        return result

    def clear(self) -> None:
        self.head = None
        self.tail = None
        self.cursor = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def __iter__(self):
        curr = self.head
        while curr is not None:
            yield curr.data
            curr = curr.next

    def __repr__(self) -> str:
        items = [repr(x) for x in self]
        return " <-> ".join(items) if items else "Empty"
