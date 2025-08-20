from typing import Dict, List


class TrieNode:
    """A node in the trie structure."""

    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.is_end_of_word = False


class Trie:
    """A trie data structure for efficient string storage and retrieval."""

    def __init__(self):
        """Initializes the trie with a root node."""
        self.root = TrieNode()

    def insert(self, word: str):
        """
        Inserts a word into the trie.
        Time complexity: O(L), where L is the length of the word.
        """
        current = self.root
        for char in word:
            # Get the node for the character, creating it if it doesn't exist
            current = current.children.setdefault(char, TrieNode())
        current.is_end_of_word = True

    def _find_words_from_node(self, node: TrieNode, prefix: str) -> List[str]:
        """
        A helper function to perform a depth-first search from a given node
        to find all words.
        """
        words = []
        if node.is_end_of_word:
            words.append(prefix)

        for char, child_node in node.children.items():
            words.extend(self._find_words_from_node(child_node, prefix + char))

        return words

    def autocomplete(self, prefix: str) -> List[str]:
        """
        Returns a list of words for autocompletion.

        If the prefix is valid, it returns all words starting with it.
        If the prefix is a misspelling, it suggests words based on the
        longest valid part of the prefix.
        If no part of the prefix is valid, it returns an empty list.
        """
        # normalize input
        prefix = (prefix or "").strip().lower()

        # If the user supplied an empty prefix (or whitespace), there's nothing
        # to autocomplete.
        if not prefix:
            return []

        # 1. Traverse the trie to find the node for the prefix
        current = self.root
        longest_valid_prefix_node = None
        longest_valid_prefix_str = ""

        for i, char in enumerate(prefix):
            if char in current.children:
                current = current.children[char]
                # Keep track of the last valid node and prefix string
                longest_valid_prefix_node = current
                longest_valid_prefix_str = prefix[: i + 1]
            else:
                # 2. If a character is not found, the full prefix doesn't exist.
                # If no part of the prefix was valid (e.g. first char mismatch),
                # return an empty list instead of returning everything under
                # the root. Otherwise, return suggestions for the longest
                # valid prefix found so far.
                if longest_valid_prefix_str == "" or longest_valid_prefix_node is None:
                    return []

                return self._find_words_from_node(
                    longest_valid_prefix_node, longest_valid_prefix_str
                )

        # 3. If the loop completes, the entire prefix is valid.
        # Find all words starting from this prefix node.
        return self._find_words_from_node(current, prefix)
