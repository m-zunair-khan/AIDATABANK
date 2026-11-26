"""
Searching Algorithms for AI Model Registry.
Project Usage:
  - Binary Search: Fast O(log n) exact lookup in sorted model lists.
  - Binary Search Range: Price and token window interval queries.
  - Linear Search: O(n) fallback on unsorted metadata.
  - Fuzzy Search: Approximate matching with edit/overlap similarity.
"""
from typing import Any, Callable, List, Optional, Tuple


def binary_search(
    arr: List[Any],
    target: Any,
    key: Optional[Callable[[Any], Any]] = None
) -> int:
    """
    Binary Search - O(log n) time on sorted array.
    Returns index of target or -1 if not found.
    """
    key_fn = key if key is not None else (lambda x: x)
    low = 0
    high = len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        mid_val = key_fn(arr[mid])

        if mid_val == target:
            return mid
        elif mid_val < target:
            low = mid + 1
        else:
            high = mid - 1

    return -1


def binary_search_range(
    arr: List[Any],
    low_bound: Any,
    high_bound: Any,
    key: Optional[Callable[[Any], Any]] = None
) -> List[Any]:
    """
    Binary Search Range - finds all items where low_bound <= key(item) <= high_bound.
    Time Complexity: O(log n + k) where k is the number of matching elements.
    Array must be sorted by key.
    """
    if not arr:
        return []

    key_fn = key if key is not None else (lambda x: x)

    # Find leftmost index >= low_bound
    l, r = 0, len(arr) - 1
    start_idx = len(arr)
    while l <= r:
        m = (l + r) // 2
        if key_fn(arr[m]) >= low_bound:
            start_idx = m
            r = m - 1
        else:
            l = m + 1

    # Find rightmost index <= high_bound
    l, r = 0, len(arr) - 1
    end_idx = -1
    while l <= r:
        m = (l + r) // 2
        if key_fn(arr[m]) <= high_bound:
            end_idx = m
            l = m + 1
        else:
            r = m - 1

    if start_idx <= end_idx and start_idx < len(arr) and end_idx >= 0:
        return arr[start_idx : end_idx + 1]
    return []


def linear_search(
    arr: List[Any],
    target: Any,
    key: Optional[Callable[[Any], Any]] = None
) -> int:
    """
    Linear Search - O(n) sequential scan.
    Returns index of first match or -1.
    """
    key_fn = key if key is not None else (lambda x: x)
    for idx, item in enumerate(arr):
        if key_fn(item) == target:
            return idx
    return -1


def fuzzy_search(
    arr: List[Any],
    query: str,
    key: Optional[Callable[[Any], Any]] = None,
    threshold: float = 0.4
) -> List[Tuple[Any, float]]:
    """
    Fuzzy string search using Jaccard bi-gram overlap and substring matching.
    Returns list of (item, score) sorted descending by score.
    """
    if not query:
        return []

    key_fn = key if key is not None else (lambda x: str(x))
    query_lower = query.lower()

    def get_bigrams(s: str) -> set:
        s_clean = s.lower()
        if len(s_clean) < 2:
            return {s_clean}
        return {s_clean[i:i+2] for i in range(len(s_clean) - 1)}

    q_bigrams = get_bigrams(query_lower)
    results = []

    for item in arr:
        target_str = str(key_fn(item)).lower()

        # Exact substring bonus
        if query_lower in target_str:
            substring_bonus = len(query_lower) / len(target_str)
            score = 0.6 + (0.4 * substring_bonus)
        else:
            t_bigrams = get_bigrams(target_str)
            union_len = len(q_bigrams.union(t_bigrams))
            if union_len == 0:
                score = 0.0
            else:
                score = len(q_bigrams.intersection(t_bigrams)) / union_len

        if score >= threshold:
            results.append((item, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
