"""
DSA Manager — Integrates all Data Structures into the backend.

This module demonstrates practical usage of:
- Trie: Autocomplete for model name search
- HashTable: Query result caching with TTL
- Stack: Filter undo system
- Queue: Review moderation queue
- CircularQueue: Recently viewed models ring buffer
- DoublyLinkedList: Browsing history (back/forward)
- LinkedList: Search query history
- MinHeap / MaxHeap: Top-K model extraction
- Sorting: merge_sort, quick_sort, multi_criteria_sort for model ranking
- Searching: binary_search, linear_search, fuzzy_search for model lookup
"""
from typing import Any, Dict, List, Optional
from dsa import (
    Trie, HashTable, Stack, Queue, CircularQueue,
    DoublyLinkedList, LinkedList, MinHeap, MaxHeap,
    merge_sort, quick_sort, binary_search, linear_search
)
from dsa.priority_queue import top_k
from dsa.searching import fuzzy_search, binary_search_range


class DSAManager:
    """Manages all DSA data structure instances per session and globally."""

    def __init__(self):
        # Trie for autocomplete (populated from DB at startup)
        self.autocomplete_trie = Trie()

        # Hash table for caching query results
        self.query_cache = HashTable(capacity=128)

        # Per-session structures (keyed by session_id)
        self._filter_stacks: Dict[str, Stack] = {}
        self._browse_history: Dict[str, DoublyLinkedList] = {}
        self._search_history: Dict[str, LinkedList] = {}
        self._recently_viewed: Dict[str, CircularQueue] = {}

        # Global review moderation queue (FIFO)
        self.review_queue = Queue()

        # Sorted model list for binary search (populated at startup)
        self._sorted_models: List[Dict[str, Any]] = []

    # ---- Autocomplete (Trie) ----
    def build_autocomplete(self, models: List[Dict[str, Any]]) -> None:
        """Populate the trie with model names and family names for strict prefix search."""
        self.autocomplete_trie.clear()
        for m in models:
            name = (m.get("version_name") or "").strip()
            fam = (m.get("family_name") or "").strip()
            if name:
                self.autocomplete_trie.insert(name.lower(), m)
            if fam and fam.lower() != name.lower():
                self.autocomplete_trie.insert(fam.lower(), m)

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Return model suggestions for a prefix using the Trie (Prefix Tree) DSA."""
        results = self.autocomplete_trie.starts_with(prefix.lower())
        suggestions = []
        seen_names = set()
        for word, data in results:
            if data and data.get("version_name") and data.get("version_name") not in seen_names:
                seen_names.add(data.get("version_name"))
                suggestions.append({
                    "name": data.get("version_name"),
                    "version_id": data.get("version_id"),
                    "provider": data.get("provider_name"),
                    "family": data.get("family_name")
                })
                if len(suggestions) >= limit:
                    break
            elif not data and word not in seen_names:
                seen_names.add(word)
                suggestions.append({"name": word})
                if len(suggestions) >= limit:
                    break
        return suggestions

    # ---- Cache (Hash Table) ----
    def cache_get(self, key: str) -> Optional[Any]:
        return self.query_cache.get(key)

    def cache_put(self, key: str, value: Any, ttl: float = 300.0) -> None:
        self.query_cache.put(key, value, ttl=ttl)

    def cache_clear(self) -> None:
        self.query_cache.clear()

    # ---- Filter Undo (Stack) ----
    def get_filter_stack(self, session_id: str) -> Stack:
        if session_id not in self._filter_stacks:
            self._filter_stacks[session_id] = Stack()
        return self._filter_stacks[session_id]

    def push_filter(self, session_id: str, filter_state: Any) -> None:
        """Push a filter onto the session's filter stack."""
        self.get_filter_stack(session_id).push(filter_state)

    def undo_filter(self, session_id: str) -> Optional[Any]:
        """Pop the last filter. Returns previous state or None."""
        stack = self.get_filter_stack(session_id)
        if stack.is_empty():
            return None
        return stack.pop()

    def get_current_filters(self, session_id: str) -> Optional[Any]:
        """Peek at current filters without removing."""
        stack = self.get_filter_stack(session_id)
        if stack.is_empty():
            return None
        return stack.peek()

    def get_filter_history(self, session_id: str) -> List[Any]:
        """Get all applied filters (top to bottom)."""
        return self.get_filter_stack(session_id).to_list()

    # ---- Browse History (Doubly Linked List) ----
    def get_browse_history(self, session_id: str) -> DoublyLinkedList:
        if session_id not in self._browse_history:
            self._browse_history[session_id] = DoublyLinkedList()
        return self._browse_history[session_id]

    def add_to_browse_history(self, session_id: str, model_data: Any) -> None:
        self.get_browse_history(session_id).append(model_data)

    def browse_forward(self, session_id: str) -> Optional[Any]:
        return self.get_browse_history(session_id).move_forward()

    def browse_backward(self, session_id: str) -> Optional[Any]:
        return self.get_browse_history(session_id).move_backward()

    def browse_current(self, session_id: str) -> Optional[Any]:
        return self.get_browse_history(session_id).current()

    # ---- Search History (Linked List) ----
    def get_search_history(self, session_id: str) -> LinkedList:
        if session_id not in self._search_history:
            self._search_history[session_id] = LinkedList()
        return self._search_history[session_id]

    def add_search(self, session_id: str, query: str) -> None:
        self.get_search_history(session_id).append(query)

    def get_searches(self, session_id: str) -> List[Any]:
        return self.get_search_history(session_id).to_list()

    # ---- Recently Viewed (Circular Queue) ----
    def get_recent_views(self, session_id: str) -> CircularQueue:
        if session_id not in self._recently_viewed:
            self._recently_viewed[session_id] = CircularQueue(capacity=10)
        return self._recently_viewed[session_id]

    def add_recent_view(self, session_id: str, model_data: Any) -> None:
        self.get_recent_views(session_id).enqueue(model_data)

    def get_recently_viewed(self, session_id: str) -> List[Any]:
        items = self.get_recent_views(session_id).to_list()
        seen = set()
        deduped = []
        for it in reversed(items):
            vid = it.get("version_id") if isinstance(it, dict) else it
            if vid not in seen:
                seen.add(vid)
                deduped.append(it)
        return list(reversed(deduped))

    # ---- Review Moderation Queue (FIFO Queue) ----
    def submit_review_for_moderation(self, review: Dict[str, Any]) -> None:
        self.review_queue.enqueue(review)

    def get_next_review_to_moderate(self) -> Optional[Any]:
        if self.review_queue.is_empty():
            return None
        return self.review_queue.dequeue()

    def pending_reviews_count(self) -> int:
        return self.review_queue.size()

    def peek_next_review(self) -> Optional[Any]:
        if self.review_queue.is_empty():
            return None
        return self.review_queue.peek()

    # ---- Top-K Models (Priority Queue / Heap) ----
    def get_top_k_models(
        self,
        models: List[Dict[str, Any]],
        k: int,
        criteria: str = "rating",
        reverse: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get top K models using heap-based priority queue.
        criteria: 'rating', 'price', 'context_length', 'release_date'
        """
        key_map = {
            "rating": lambda m: float(m.get("avg_rating") or 0),
            "price": lambda m: float(m.get("input_price_per_1m_tokens") or m.get("input_price") or 0),
            "context_length": lambda m: int(m.get("context_length") or 0),
            "release_date": lambda m: str(m.get("release_date") or ""),
        }
        key_fn = key_map.get(criteria, key_map["rating"])
        return top_k(models, k, key=key_fn, reverse=reverse)

    # ---- Sorting (Merge Sort, Quick Sort) ----
    def sort_models(
        self,
        models: List[Dict[str, Any]],
        sort_by: str = "price",
        order: str = "asc",
        algorithm: str = "merge"
    ) -> List[Dict[str, Any]]:
        """
        Sort models using pure Python DSA sorting algorithms.
        algorithm: 'merge' (stable, recommended) or 'quick' (fast partitioning)
        """
        key_map = {
            "price": lambda m: float(m.get("input_price_per_1m_tokens") or m.get("input_price") or 0),
            "output_price": lambda m: float(m.get("output_price_per_1m_tokens") or m.get("output_price") or 0),
            "rating": lambda m: float(m.get("avg_rating") or 0),
            "context_length": lambda m: int(m.get("context_length") or 0),
            "release_date": lambda m: str(m.get("release_date") or ""),
            "name": lambda m: str(m.get("version_name") or "").lower(),
            "lab": lambda m: str(m.get("provider_name") or "").lower(),
        }
        key_fn = key_map.get(sort_by, key_map["name"])
        reverse = (order == "desc")

        if algorithm == "merge":
            return merge_sort(models, key=key_fn, reverse=reverse)
        else:
            return quick_sort(models, key=key_fn, reverse=reverse)

    # ---- Searching (Binary Search, Linear Search, Fuzzy Search) ----
    def build_sorted_index(self, models: List[Dict[str, Any]]) -> None:
        """Build sorted list of models for binary search."""
        self._sorted_models = merge_sort(
            models,
            key=lambda m: str(m.get("version_name") or "").lower()
        )

    def search_model_binary(self, name: str) -> Optional[Dict[str, Any]]:
        """Binary search for exact model name match. O(log n)."""
        idx = binary_search(
            self._sorted_models,
            name.lower(),
            key=lambda m: str(m.get("version_name") or "").lower()
        )
        return self._sorted_models[idx] if idx != -1 else None

    def search_model_linear(self, name: str) -> Optional[Dict[str, Any]]:
        """Linear search for model name. O(n)."""
        idx = linear_search(
            self._sorted_models,
            name.lower(),
            key=lambda m: str(m.get("version_name") or "").lower()
        )
        return self._sorted_models[idx] if idx != -1 else None

    def search_models_fuzzy(self, query: str) -> List[Any]:
        """Fuzzy search for model names with similarity scoring."""
        return fuzzy_search(
            self._sorted_models,
            query,
            key=lambda m: str(m.get("version_name") or ""),
            threshold=0.3
        )

    def search_models_by_price_range(self, min_price: float, max_price: float) -> List[Dict[str, Any]]:
        """Binary search range on price-sorted models."""
        price_sorted = merge_sort(
            self._sorted_models,
            key=lambda m: float(m.get("input_price_per_1m_tokens") or m.get("input_price") or 0)
        )
        return binary_search_range(
            price_sorted,
            min_price,
            max_price,
            key=lambda m: float(m.get("input_price_per_1m_tokens") or m.get("input_price") or 0)
        )

    def cleanup_session(self, session_id: str) -> None:
        """Clear all session data structures."""
        self._filter_stacks.pop(session_id, None)
        self._browse_history.pop(session_id, None)
        self._search_history.pop(session_id, None)
        self._recently_viewed.pop(session_id, None)


# Global singleton
dsa_manager = DSAManager()
