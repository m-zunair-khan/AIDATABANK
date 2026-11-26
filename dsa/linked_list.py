"""
Singly Linked List implementation.
Project Usage: Search history tracking. Each search query is stored as a node in the list.
Time Complexity:
  - append: O(1) with tail pointer
  - prepend: O(1)
  - delete: O(n)
  - search: O(n)
  - traversal / to_list: O(n)
"""
from typing import Any, List, Optional


class Node:
    """A node in a singly linked list."""
    def __init__(self, data: Any, next_node: Optional['Node'] = None):
        self.data = data
        self.next = next_node

    def __repr__(self) -> str:
        return f"Node({self.data!r})"


class LinkedList:
    """
    Singly linked list with head and tail pointers.
    Maintains search query history per user session.
    """
    def __init__(self):
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self._size: int = 0

    def append(self, data: Any) -> None:
        """Add node to the end of the list. O(1) time."""
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            assert self.tail is not None
            self.tail.next = new_node
            self.tail = new_node
        self._size += 1

    def prepend(self, data: Any) -> None:
        """Add node to the beginning of the list. O(1) time."""
        new_node = Node(data, self.head)
        self.head = new_node
        if self.tail is None:
            self.tail = new_node
        self._size += 1

    def delete(self, data: Any) -> bool:
        """Delete the first occurrence of data. O(n) time. Returns True if deleted."""
        curr = self.head
        prev: Optional[Node] = None
        while curr is not None:
            if curr.data == data:
                if prev is None:
                    self.head = curr.next
                    if self.head is None:
                        self.tail = None
                else:
                    prev.next = curr.next
                    if curr == self.tail:
                        self.tail = prev
                self._size -= 1
                return True
            prev = curr
            curr = curr.next
        return False

    def search(self, data: Any) -> bool:
        """Search for data in the list. O(n) time."""
        curr = self.head
        while curr is not None:
            if curr.data == data:
                return True
            curr = curr.next
        return False

    def to_list(self) -> List[Any]:
        """Convert linked list to Python list. O(n) time."""
        result = []
        curr = self.head
        while curr is not None:
            result.append(curr.data)
            curr = curr.next
        return result

    def clear(self) -> None:
        """Clear all nodes from the list."""
        self.head = None
        self.tail = None
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
        return " -> ".join(items) + (" -> None" if items else "Empty")
