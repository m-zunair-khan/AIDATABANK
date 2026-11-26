"""
Sorting Algorithms for AI Model Registry.
Project Usage: Multi-criteria and dynamic in-memory ranking of AI models
(e.g., sorting by cost, context window, benchmark scores, or combinations).
Algorithms:
  - Merge Sort: O(n log n) time, stable. Essential for multi-criteria sorting.
  - Quick Sort: O(n log n) avg time, in-place / partition based.
  - Insertion Sort: O(n^2) worst case, O(n) best for nearly sorted data.
"""
from typing import Any, Callable, List, Optional, Tuple


def merge_sort(
    arr: List[Any],
    key: Optional[Callable[[Any], Any]] = None,
    reverse: bool = False
) -> List[Any]:
    """
    Merge Sort - Stable O(n log n) algorithm.
    Returns a new sorted list.
    """
    if len(arr) <= 1:
        return list(arr)

    key_fn = key if key is not None else (lambda x: x)

    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key=key, reverse=reverse)
    right = merge_sort(arr[mid:], key=key, reverse=reverse)

    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        val_l = key_fn(left[i])
        val_r = key_fn(right[j])

        condition = (val_l > val_r) if reverse else (val_l <= val_r)
        if condition:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def quick_sort(
    arr: List[Any],
    key: Optional[Callable[[Any], Any]] = None,
    reverse: bool = False
) -> List[Any]:
    """
    Quick Sort - O(n log n) average time algorithm.
    Returns a new sorted list.
    """
    if len(arr) <= 1:
        return list(arr)

    key_fn = key if key is not None else (lambda x: x)
    pivot = arr[len(arr) // 2]
    pivot_val = key_fn(pivot)

    less = []
    equal = []
    greater = []

    for item in arr:
        val = key_fn(item)
        if val < pivot_val:
            less.append(item)
        elif val > pivot_val:
            greater.append(item)
        else:
            equal.append(item)

    if reverse:
        return quick_sort(greater, key=key, reverse=True) + equal + quick_sort(less, key=key, reverse=True)
    else:
        return quick_sort(less, key=key, reverse=False) + equal + quick_sort(greater, key=key, reverse=False)


def insertion_sort(
    arr: List[Any],
    key: Optional[Callable[[Any], Any]] = None,
    reverse: bool = False
) -> List[Any]:
    """
    Insertion Sort - O(n^2) worst case, O(n) best case for nearly-sorted lists.
    Returns a new sorted list.
    """
    result = list(arr)
    key_fn = key if key is not None else (lambda x: x)

    for i in range(1, len(result)):
        current = result[i]
        curr_val = key_fn(current)
        j = i - 1

        while j >= 0:
            compare_val = key_fn(result[j])
            condition = (curr_val > compare_val) if reverse else (curr_val < compare_val)
            if condition:
                result[j + 1] = result[j]
                j -= 1
            else:
                break
        result[j + 1] = current

    return result


def multi_criteria_sort(
    arr: List[Any],
    criteria: List[Tuple[Callable[[Any], Any], bool]]
) -> List[Any]:
    """
    Stable multi-criteria sorting using successive passes of Merge Sort.
    criteria: list of (key_func, reverse_bool) from highest priority to lowest priority.
    Applies criteria in reverse order to maintain stability.
    """
    result = list(arr)
    for key_fn, reverse in reversed(criteria):
        result = merge_sort(result, key=key_fn, reverse=reverse)
    return result
