"""String encoding with official TOON quoting rules.

Implements the string quoting and escaping rules from the official TOON specification.
Strings are only quoted when necessary to avoid ambiguity.
"""

from toonverter.core.spec import (
    ESCAPE_CHARS,
    NUMBER_PATTERN,
    QUOTE_REQUIRED_CHARS,
    RESERVED_WORDS,
    Delimiter,
)


class StringEncoder:
    """Encoder for strings following TOON specification quoting rules.

    The TOON spec requires minimal quoting - only when the string:
    - Is empty
    - Has leading/trailing whitespace
    - Matches a reserved word (true, false, null)
    - Looks like a number
    - Contains special characters
    - Contains the active delimiter
    - Equals or starts with "-"
    """

    _TRANS_TABLE = str.maketrans(ESCAPE_CHARS)

    def __init__(self, delimiter: Delimiter) -> None:
        """Initialize string encoder.

        Args:
            delimiter: Active delimiter for arrays/fields
        """
        self.delimiter = delimiter.value

    def encode(self, s: str) -> str:
        """Encode string, adding quotes if necessary.

        Args:
            s: String to encode

        Returns:
            Encoded string (quoted if necessary)

        Examples:
            >>> encoder = StringEncoder(Delimiter.COMMA)
            >>> encoder.encode("hello")
            'hello'
            >>> encoder.encode("true")
            '"true"'
            >>> encoder.encode("hello world")
            'hello world'
            >>> encoder.encode("hello: world")
            '"hello: world"'
        """
        if self._needs_quoting(s):
            return self._quote_and_escape(s)
        return s

    def _needs_quoting(self, s: str) -> bool:
        """Check if string requires quotes per TOON spec.

        Args:
            s: String to check

        Returns:
            True if string needs quotes, False otherwise
        """
        # Empty string needs quotes
        if not s:
            return True

        # Equals dash or starts with dash (could be confused with list item)
        # Per TOON v2.0 spec: always quote strings equal to or starting with "-"
        if s.startswith("-"):
            return True

        # Leading or trailing whitespace
        if s[0].isspace() or s[-1].isspace():
            return True

        # Contains structural characters that need quoting or delimiter
        # Combined check for efficiency
        if any(c in QUOTE_REQUIRED_CHARS or c == self.delimiter for c in s):
            return True

        # Reserved words (case-insensitive)
        if s.lower() in RESERVED_WORDS:
            return True

        # Looks like a number
        return bool(NUMBER_PATTERN.match(s))

    def _quote_and_escape(self, s: str) -> str:
        """Add quotes and escape special characters.

        Only 5 escape sequences are valid in TOON:
        - \\ (backslash)
        - \" (double quote)
        - \\n (newline)
        - \\r (carriage return)
        - \\t (tab)

        Args:
            s: String to quote and escape

        Returns:
            Quoted and escaped string

        Examples:
            >>> encoder = StringEncoder(Delimiter.COMMA)
            >>> encoder._quote_and_escape('hello\\nworld')
            '"hello\\\\nworld"'
            >>> encoder._quote_and_escape('say "hi"')
            '"say \\\\"hi\\\\""'
        """
        return f'"{s.translate(self._TRANS_TABLE)}"'

    def decode(self, s: str) -> str:
        """Decode potentially quoted string.

        Args:
            s: String to decode (may or may not be quoted)

        Returns:
            Decoded string

        Raises:
            ValueError: If escape sequence is invalid

        Examples:
            >>> encoder = StringEncoder(Delimiter.COMMA)
            >>> encoder.decode('"hello"')
            'hello'
            >>> encoder.decode('unquoted')
            'unquoted'
        """
        # Check if quoted
        if s.startswith('"') and s.endswith('"') and len(s) >= 2:
            return self._unescape(s[1:-1])
        return s

    def _unescape(self, s: str) -> str:
        """Unescape escaped characters.

        Args:
            s: Escaped string content (without outer quotes)

        Returns:
            Unescaped string

        Raises:
            ValueError: If invalid escape sequence found
        """
        result = []
        i = 0
        while i < len(s):
            if s[i] == "\\":
                if i + 1 >= len(s):
                    msg = "Unterminated escape sequence at end of string"
                    raise ValueError(msg)

                next_char = s[i + 1]

                # Only 5 valid escapes
                if next_char == "\\":
                    result.append("\\")
                elif next_char == '"':
                    result.append('"')
                elif next_char == "n":
                    result.append("\n")
                elif next_char == "r":
                    result.append("\r")
                elif next_char == "t":
                    result.append("\t")
                else:
                    msg = (
                        f"Invalid escape sequence: \\{next_char}. "
                        f'Only \\\\, \\", \\n, \\r, \\t are allowed.'
                    )
                    raise ValueError(msg)

                i += 2
            else:
                result.append(s[i])
                i += 1

        return "".join(result)
