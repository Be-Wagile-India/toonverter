"""Indentation management for TOON encoding.

TOON uses indentation-based structure like YAML:
- 2 spaces per level by default
- Tabs are forbidden for indentation (only in quoted strings or as delimiter)
- Consistent indentation required
"""

from toonverter.core.spec import DEFAULT_INDENT_SIZE, INDENT_CHAR


class IndentationManager:
    """Manage indentation levels for TOON output.

    This class tracks the current depth and generates appropriate
    indentation strings for the TOON format.
    """

    def __init__(self, indent_size: int = DEFAULT_INDENT_SIZE) -> None:
        """Initialize indentation manager.

        Args:
            indent_size: Number of spaces per indentation level (default: 2)

        Raises:
            ValueError: If indent_size is less than 1
        """
        if indent_size < 1:
            msg = "indent_size must be at least 1"
            raise ValueError(msg)

        self.indent_size = indent_size
        self.current_depth = 0

    def indent(self, depth: int) -> str:
        """Get indentation string for a specific depth level.

        Args:
            depth: Indentation depth (0 = no indent, 1 = one level, etc.)

        Returns:
            Indentation string (spaces only)

        Examples:
            >>> mgr = IndentationManager(indent_size=2)
            >>> mgr.indent(0)
            ''
            >>> mgr.indent(1)
            '  '
            >>> mgr.indent(2)
            '    '
        """
        depth = max(depth, 0)
        return INDENT_CHAR * (depth * self.indent_size)

    def push(self) -> int:
        """Increase indentation depth by one level.

        Returns:
            New depth level

        Examples:
            >>> mgr = IndentationManager()
            >>> mgr.current_depth
            0
            >>> mgr.push()
            1
            >>> mgr.push()
            2
        """
        self.current_depth += 1
        return self.current_depth

    def pop(self) -> int:
        """Decrease indentation depth by one level.

        Returns:
            New depth level (minimum 0)

        Examples:
            >>> mgr = IndentationManager()
            >>> mgr.current_depth = 2
            >>> mgr.pop()
            1
            >>> mgr.pop()
            0
            >>> mgr.pop()  # Can't go below 0
            0
        """
        if self.current_depth > 0:
            self.current_depth -= 1
        return self.current_depth

    def reset(self) -> None:
        """Reset depth to 0.

        Examples:
            >>> mgr = IndentationManager()
            >>> mgr.current_depth = 5
            >>> mgr.reset()
            >>> mgr.current_depth
            0
        """
        self.current_depth = 0

    def get_current_indent(self) -> str:
        """Get indentation string for current depth.

        Returns:
            Indentation string for current depth

        Examples:
            >>> mgr = IndentationManager(indent_size=2)
            >>> mgr.current_depth = 2
            >>> mgr.get_current_indent()
            '    '
        """
        return self.indent(self.current_depth)


def detect_indentation(line: str) -> int:
    """Detect indentation level of a line.

    Args:
        line: Line of TOON text

    Returns:
        Number of leading spaces

    Raises:
        ValueError: If line contains tab characters for indentation

    Examples:
        >>> detect_indentation("name: Alice")
        0
        >>> detect_indentation("  age: 30")
        2
        >>> detect_indentation("    city: NYC")
        4
    """
    # Count leading spaces
    spaces = 0
    for char in line:
        if char == " ":
            spaces += 1
        elif char == "\t":
            msg = "Tab characters are not allowed for indentation in TOON format. Use spaces only."
            raise ValueError(msg)
        else:
            break

    return spaces


def calculate_depth(spaces: int, indent_size: int = DEFAULT_INDENT_SIZE) -> int:
    """Calculate depth level from number of spaces.

    Args:
        spaces: Number of leading spaces
        indent_size: Spaces per indentation level

    Returns:
        Depth level

    Raises:
        ValueError: If spaces is not a multiple of indent_size (in strict mode)

    Examples:
        >>> calculate_depth(0, 2)
        0
        >>> calculate_depth(2, 2)
        1
        >>> calculate_depth(4, 2)
        2
        >>> calculate_depth(3, 2)  # Not exact multiple
        1
    """
    if spaces == 0:
        return 0

    # Calculate depth
    return spaces // indent_size

    # In strict mode, check for exact multiples
    # For now, we allow non-exact multiples (truncate)
