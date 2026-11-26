"""
Trie (Prefix Tree) implementation.
Project Usage: Model search autocomplete. Users type a model prefix (e.g., "claude", "gpt-4"),
and the Trie returns all matching model records in O(p + k) time.
Time Complexity:
  - insert: O(L) where L is string length
  - search: O(L)
  - starts_with (prefix search): O(P + K) where P is prefix length, K is total matches
"""
from typing import Any, Dict, List, Optional, Tuple


class TrieNode:
    """Node in the prefix tree."""
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end_of_word: bool = False
        self.data: Any = None


class Trie:
    """Trie structure for fast autocomplete and prefix matching."""
    def __init__(self):
        self.root = TrieNode()
        self._count = 0

    def insert(self, word: str, data: Any = None) -> None:
        """Insert a word with optional attached model data. O(L) time."""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        if not node.is_end_of_word:
            self._count += 1
        node.is_end_of_word = True
        node.data = data

    def search(self, word: str) -> bool:
        """Check if an exact word exists in Trie. O(L) time."""
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word

    def get_data(self, word: str) -> Optional[Any]:
        """Get attached data for an exact word."""
        node = self.root
        for char in word:
            if char not in node.children:
                return None
            node = node.children[char]
        return node.data if node.is_end_of_word else None

    def starts_with(self, prefix: str) -> List[Tuple[str, Any]]:
        """
        Find all words and attached data starting with prefix.
        Returns: list of (word, data) tuples.
        """
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        results: List[Tuple[str, Any]] = []
        self._dfs(node, prefix, results)
        return results

    def _dfs(self, node: TrieNode, path: str, results: List[Tuple[str, Any]]) -> None:
        if node.is_end_of_word:
            results.append((path, node.data))
        for char, child_node in node.children.items():
            self._dfs(child_node, path + char, results)

    def delete(self, word: str) -> bool:
        """Delete word from Trie. O(L) time."""
        def _delete(node: TrieNode, w: str, depth: int) -> bool:
            if depth == len(w):
                if not node.is_end_of_word:
                    return False
                node.is_end_of_word = False
                node.data = None
                return len(node.children) == 0

            char = w[depth]
            if char not in node.children:
                return False

            should_delete_child = _delete(node.children[char], w, depth + 1)
            if should_delete_child:
                del node.children[char]
                return len(node.children) == 0 and not node.is_end_of_word
            return False

        if not word:
            return False
        deleted = _delete(self.root, word, 0)
        if deleted or not self.search(word):
            self._count = max(0, self._count - 1)
            return True
        return False

    def all_words(self) -> List[Tuple[str, Any]]:
        """Return all words in the Trie."""
        results: List[Tuple[str, Any]] = []
        self._dfs(self.root, "", results)
        return results

    def clear(self) -> None:
        self.root = TrieNode()
        self._count = 0

    def __len__(self) -> int:
        return self._count

    def __contains__(self, word: str) -> bool:
        return self.search(word)
