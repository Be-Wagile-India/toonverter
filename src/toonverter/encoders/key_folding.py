"""Key folding logic for TOON format.

Key folding collapses single-key object chains into dotted notation:
    a.b.c: value
instead of:
    a:
      b:
        c: value
"""

from typing import Any

from ..core.spec import KEY_FOLD_SEPARATOR, KEY_SEGMENT_PATTERN, KeyPath


class KeyFolder:
    """Handle key folding transformations."""

    def __init__(self, enabled: bool = False) -> None:
        """Initialize key folder.

        Args:
            enabled: Whether key folding is enabled
        """
        self.enabled = enabled

    def can_fold_chain(self, obj: dict[str, Any]) -> tuple[bool, list[str]]:
        """Check if object is a single-key chain that can be folded.

        Args:
            obj: Dictionary to check

        Returns:
            Tuple of (can_fold, key_chain)

        Examples:
            >>> folder = KeyFolder(enabled=True)
            >>> folder.can_fold_chain({"a": {"b": {"c": 1}}})
            (True, ['a', 'b', 'c'])
            >>> folder.can_fold_chain({"a": 1, "b": 2})
            (False, [])
        """
        if not self.enabled:
            return False, []

        key_chain = []
        current = obj

        # Traverse single-key chains
        while isinstance(current, dict) and len(current) == 1:
            key = list(current.keys())[0]

            # Check if key is a valid identifier segment
            if not KEY_SEGMENT_PATTERN.match(key):
                break

            # Check if key contains the separator (can't fold)
            if KEY_FOLD_SEPARATOR in key:
                break

            key_chain.append(key)
            current = current[key]

            # If we hit a non-dict, we're done
            if not isinstance(current, dict):
                break

        # Can fold if we have a chain of 2+ keys
        return len(key_chain) >= 2, key_chain

    def fold_key_chain(self, key_chain: list[str]) -> str:
        """Fold key chain into dotted notation.

        Args:
            key_chain: List of keys to fold

        Returns:
            Folded key string

        Examples:
            >>> folder = KeyFolder()
            >>> folder.fold_key_chain(['a', 'b', 'c'])
            'a.b.c'
        """
        return KEY_FOLD_SEPARATOR.join(key_chain)

    def get_folded_value(self, obj: dict[str, Any], key_chain: list[str]) -> Any:
        """Get the value at the end of a key chain.

        Args:
            obj: Root object
            key_chain: Chain of keys to traverse

        Returns:
            Value at end of chain

        Examples:
            >>> folder = KeyFolder()
            >>> folder.get_folded_value({"a": {"b": 1}}, ['a', 'b'])
            1
        """
        current = obj
        for key in key_chain:
            current = current[key]
        return current

    def detect_foldable_keys(self, obj: dict[str, Any]) -> list[tuple[str, list[str], Any]]:
        """Detect all foldable key chains in an object.

        Args:
            obj: Object to analyze

        Returns:
            List of (folded_key, key_chain, value) tuples

        Examples:
            >>> folder = KeyFolder(enabled=True)
            >>> obj = {"a": {"b": 1}, "c": {"d": {"e": 2}}}
            >>> folder.detect_foldable_keys(obj)
            [('a.b', ['a', 'b'], 1), ('c.d.e', ['c', 'd', 'e'], 2)]
        """
        if not self.enabled:
            return []

        foldable = []

        for key, value in obj.items():
            if isinstance(value, dict):
                # Check if this starts a foldable chain
                chain_obj = {key: value}
                can_fold, key_chain = self.can_fold_chain(chain_obj)

                if can_fold:
                    folded_key = self.fold_key_chain(key_chain)
                    final_value = self.get_folded_value(chain_obj, key_chain)
                    foldable.append((folded_key, key_chain, final_value))

        return foldable

    def unfold_key(self, folded_key: str, value: Any) -> dict[str, Any]:
        """Unfold a dotted key into nested objects.

        Args:
            folded_key: Folded key like "a.b.c"
            value: Value to assign

        Returns:
            Nested dict structure

        Examples:
            >>> folder = KeyFolder()
            >>> folder.unfold_key("a.b.c", 1)
            {'a': {'b': {'c': 1}}}
        """
        segments = folded_key.split(KEY_FOLD_SEPARATOR)

        # Build from innermost to outermost
        result: dict[str, Any] = {segments[-1]: value}

        for segment in reversed(segments[:-1]):
            result = {segment: result}

        return result

    def should_fold_key(self, key: str, value: Any, siblings: dict[str, Any]) -> bool:
        """Check if a specific key should be folded.

        Args:
            key: Key to check
            value: Value for this key
            siblings: All sibling keys in the object

        Returns:
            True if key should be folded

        Rules:
            - Key folding must be enabled
            - Value must be a dict
            - No collisions with sibling keys
            - Must form valid identifier chain
        """
        if not self.enabled:
            return False

        if not isinstance(value, dict):
            return False

        # Check for collisions
        if self._has_collision(key, siblings):
            return False

        # Check if it forms a valid foldable chain
        can_fold, _ = self.can_fold_chain({key: value})
        return can_fold

    def _has_collision(self, key: str, siblings: dict[str, Any]) -> bool:
        """Check if folding this key would create a collision.

        Args:
            key: Key to fold
            siblings: Sibling keys

        Returns:
            True if collision detected
        """
        # If any sibling key starts with "key.", it would collide
        prefix = f"{key}{KEY_FOLD_SEPARATOR}"
        return any(sibling.startswith(prefix) for sibling in siblings if sibling != key)
