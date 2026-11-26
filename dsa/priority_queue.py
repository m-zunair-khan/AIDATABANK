"""
Priority Queue (Binary Heap: Min-Heap and Max-Heap) implementation.
Project Usage: Extract top-K AI models based on custom metrics (cheapest price, highest arena score, etc.).
Time Complexity:
  - insert: O(log n)
  - extract: O(log n)
  - peek: O(1)
  - build heap / top_k: O(n log k)
"""
from typing import Any, Callable, List, Optional, Tuple


class MinHeap:
    """Array-based binary min-heap storing tuples of (priority, data)."""
    def __init__(self):
        self._heap: List[Tuple[Any, Any]] = []

    def insert(self, priority: Any, data: Any) -> None:
        """Insert element with priority. O(log n) time."""
        self._heap.append((priority, data))
        self._sift_up(len(self._heap) - 1)

    def extract(self) -> Tuple[Any, Any]:
        """Remove and return minimum (priority, data). O(log n) time."""
        if self.is_empty():
            raise IndexError("extract from empty heap")
        if len(self._heap) == 1:
            return self._heap.pop()
        min_elem = self._heap[0]
        self._heap[0] = self._heap.pop()
        self._sift_down(0)
        return min_elem

    def peek(self) -> Tuple[Any, Any]:
        """View minimum without removing. O(1) time."""
        if self.is_empty():
            raise IndexError("peek from empty heap")
        return self._heap[0]

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def size(self) -> int:
        return len(self._heap)

    def to_sorted_list(self) -> List[Tuple[Any, Any]]:
        """Extract all elements in ascending priority order."""
        copy_heap = MinHeap()
        copy_heap._heap = list(self._heap)
        res = []
        while not copy_heap.is_empty():
            res.append(copy_heap.extract())
        return res

    def _sift_up(self, idx: int) -> None:
        parent = (idx - 1) // 2
        while idx > 0 and self._heap[idx][0] < self._heap[parent][0]:
            self._heap[idx], self._heap[parent] = self._heap[parent], self._heap[idx]
            idx = parent
            parent = (idx - 1) // 2

    def _sift_down(self, idx: int) -> None:
        size = len(self._heap)
        while True:
            left = 2 * idx + 1
            right = 2 * idx + 2
            smallest = idx
            if left < size and self._heap[left][0] < self._heap[smallest][0]:
                smallest = left
            if right < size and self._heap[right][0] < self._heap[smallest][0]:
                smallest = right
            if smallest != idx:
                self._heap[idx], self._heap[smallest] = self._heap[smallest], self._heap[idx]
                idx = smallest
            else:
                break

    def __len__(self) -> int:
        return len(self._heap)


class MaxHeap:
    """Array-based binary max-heap storing tuples of (priority, data)."""
    def __init__(self):
        self._heap: List[Tuple[Any, Any]] = []

    def insert(self, priority: Any, data: Any) -> None:
        """Insert element with priority. O(log n) time."""
        self._heap.append((priority, data))
        self._sift_up(len(self._heap) - 1)

    def extract(self) -> Tuple[Any, Any]:
        """Remove and return maximum (priority, data). O(log n) time."""
        if self.is_empty():
            raise IndexError("extract from empty heap")
        if len(self._heap) == 1:
            return self._heap.pop()
        max_elem = self._heap[0]
        self._heap[0] = self._heap.pop()
        self._sift_down(0)
        return max_elem

    def peek(self) -> Tuple[Any, Any]:
        """View maximum without removing. O(1) time."""
        if self.is_empty():
            raise IndexError("peek from empty heap")
        return self._heap[0]

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def size(self) -> int:
        return len(self._heap)

    def to_sorted_list(self) -> List[Tuple[Any, Any]]:
        """Extract all elements in descending priority order."""
        copy_heap = MaxHeap()
        copy_heap._heap = list(self._heap)
        res = []
        while not copy_heap.is_empty():
            res.append(copy_heap.extract())
        return res

    def _sift_up(self, idx: int) -> None:
        parent = (idx - 1) // 2
        while idx > 0 and self._heap[idx][0] > self._heap[parent][0]:
            self._heap[idx], self._heap[parent] = self._heap[parent], self._heap[idx]
            idx = parent
            parent = (idx - 1) // 2

    def _sift_down(self, idx: int) -> None:
        size = len(self._heap)
        while True:
            left = 2 * idx + 1
            right = 2 * idx + 2
            largest = idx
            if left < size and self._heap[left][0] > self._heap[largest][0]:
                largest = left
            if right < size and self._heap[right][0] > self._heap[largest][0]:
                largest = right
            if largest != idx:
                self._heap[idx], self._heap[largest] = self._heap[largest], self._heap[idx]
                idx = largest
            else:
                break

    def __len__(self) -> int:
        return len(self._heap)


def top_k(items: List[Any], k: int, key: Optional[Callable[[Any], Any]] = None, reverse: bool = False) -> List[Any]:
    """
    Extract top-K items from an iterable using a heap.
    Complexity: O(n log k) time, O(k) space.
    If reverse is False, returns highest k values (descending order).
    If reverse is True, returns lowest k values (ascending order).
    """
    if k <= 0 or not items:
        return []
    
    key_func = key if key is not None else (lambda x: x)
    
    if reverse:
        # We want smallest k items: maintain max-heap of size k
        heap = MaxHeap()
        for item in items:
            p = key_func(item)
            if heap.size() < k:
                heap.insert(p, item)
            else:
                if p < heap.peek()[0]:
                    heap.extract()
                    heap.insert(p, item)
        # Result sorted ascending
        extracted = []
        while not heap.is_empty():
            extracted.append(heap.extract()[1])
        return list(reversed(extracted))
    else:
        # We want largest k items: maintain min-heap of size k
        heap = MinHeap()
        for item in items:
            p = key_func(item)
            if heap.size() < k:
                heap.insert(p, item)
            else:
                if p > heap.peek()[0]:
                    heap.extract()
                    heap.insert(p, item)
        # Result sorted descending
        extracted = []
        while not heap.is_empty():
            extracted.append(heap.extract()[1])
        return list(reversed(extracted))
