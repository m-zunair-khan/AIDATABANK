"""
DSA (Data Structures & Algorithms) Module for AI Model Registry
================================================================

This package provides pure-Python implementations of core data structures
and algorithms used throughout the AI Model Registry backend:

- LinkedList:       Search history traversal
- DoublyLinkedList: Model browsing with forward/backward navigation
- Stack:            Filter undo system
- Queue:            Review moderation (FIFO processing)
- CircularQueue:    Recently-viewed-models ring buffer
- MinHeap/MaxHeap:  Top-K model extraction
- HashTable:        Query result caching with TTL
- Trie:             Autocomplete for model name search
- Sorting:          Multi-criteria model ranking
- Searching:        Fast model lookup (binary, linear, fuzzy)
"""

from .linked_list import LinkedList
from .doubly_linked_list import DoublyLinkedList
from .stack import Stack
from .queue_ds import Queue
from .circular_queue import CircularQueue
from .priority_queue import MinHeap, MaxHeap
from .hash_table import HashTable
from .trie import Trie
from .sorting import merge_sort, quick_sort, insertion_sort
from .searching import binary_search, linear_search
