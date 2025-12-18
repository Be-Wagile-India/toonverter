"""Lexer for TOON v2.0 format.

Tokenizes TOON input into structured tokens for parsing.
Handles indentation tracking, line-by-line scanning, and token classification.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

from toonverter.encoders.indentation import detect_indentation


class TokenType(Enum):
    """Token types in TOON format."""

    # Structural
    INDENT = "indent"
    DEDENT = "dedent"
    NEWLINE = "newline"
    EOF = "eof"

    # Literals
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    NULL = "null"

    # Symbols
    COLON = "colon"  # :
    COMMA = "comma"  # ,
    DASH = "dash"  # - (list item marker)
    COMMENT = "comment"  # # (comment marker)

    # Array markers
    ARRAY_START = "array_start"  # [
    ARRAY_END = "array_end"  # ]
    BRACE_START = "brace_start"  # {
    BRACE_END = "brace_end"  # }
    STAR = "star"  # * (for indefinite length)

    # Special
    IDENTIFIER = "identifier"  # Unquoted key or value
    QUOTED_STRING = "quoted_string"  # "value"


@dataclass
class Token:
    """A single token in TOON format."""

    type: TokenType
    value: str | int | float | bool | None
    line: int
    column: int
    indent_level: int = 0

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"


class ToonLexer:
    """Lexer for tokenizing TOON format strings.

    Converts TOON text into a stream of tokens that can be parsed.
    """

    def __init__(self, text: str, indent_size: int = 2) -> None:
        """Initialize lexer.

        Args:
            text: TOON formatted text
            indent_size: Number of spaces per indent level
        """
        self.text = text
        self.indent_size = indent_size
        self.lines = text.split("\n")
        self.current_line = 0
        self.current_column = 0
        self.current_indent = 0
        self.indent_stack: list[int] = [0]

    def tokenize(self) -> Iterator[Token]:
        """Tokenize entire input.

        Yields:
            Tokens one by one
        """
        self.current_indent = 0
        for line_num, line in enumerate(self.lines):
            self.current_line = line_num
            self.current_column = 0

            stripped_line = line.strip()

            # Skip empty lines and comment-only lines for indentation state changes
            is_content_line = bool(stripped_line) and not stripped_line.startswith("#")

            if is_content_line:
                # Handle indentation for content lines
                indent = detect_indentation(line)
                indent_level = indent // self.indent_size

                # Emit indent/dedent tokens
                if indent_level > self.current_indent:
                    for _ in range(indent_level - self.current_indent):
                        yield Token(
                            type=TokenType.INDENT,
                            value=None,
                            line=line_num,
                            column=0,
                            indent_level=self.current_indent + 1,
                        )
                        self.current_indent += 1
                elif indent_level < self.current_indent:
                    for _ in range(self.current_indent - indent_level):
                        yield Token(
                            type=TokenType.DEDENT,
                            value=None,
                            line=line_num,
                            column=0,
                            indent_level=self.current_indent - 1,
                        )
                        self.current_indent -= 1

            # Tokenize line content.
            yield from self._tokenize_line(line.lstrip(), line_num, self.current_indent)

            # Add newline token
            yield Token(
                type=TokenType.NEWLINE,
                value=None,
                line=line_num,
                column=len(line),
                indent_level=self.current_indent,
            )

        # Add final dedents if needed
        while self.current_indent > 0:
            self.current_indent -= 1
            yield Token(
                type=TokenType.DEDENT,
                value=None,
                line=len(self.lines),
                column=0,
                indent_level=self.current_indent,
            )

        # Add EOF token
        yield Token(
            type=TokenType.EOF,
            value=None,
            line=len(self.lines),
            column=0,
            indent_level=0,
        )

    def _tokenize_line(self, line: str, line_num: int, indent_level: int) -> Iterator[Token]:
        """Tokenize a single line.

        Args:
            line: Line content (stripped)
            line_num: Line number
            indent_level: Current indent level

        Yields:
            Tokens for this line
        """
        i = 0

        while i < len(line):
            char = line[i]

            # Skip whitespace
            if char in (" ", "\t"):
                i += 1
                continue

            # Colon
            if char == ":":
                yield Token(
                    type=TokenType.COLON,
                    value=":",
                    line=line_num,
                    column=i,
                    indent_level=indent_level,
                )
                i += 1
                continue

            # Comma
            if char == ",":
                yield Token(
                    type=TokenType.COMMA,
                    value=",",
                    line=line_num,
                    column=i,
                    indent_level=indent_level,
                )
                i += 1
                continue

            # Dash (list marker)
            if char == "-" and (i == 0 or line[i - 1] in (" ", "\t")):
                # Check if it's a list marker (followed by space)
                if i + 1 < len(line) and line[i + 1] == " ":
                    yield Token(
                        type=TokenType.DASH,
                        value="-",
                        line=line_num,
                        column=i,
                        indent_level=indent_level,
                    )
                    i += 2  # Skip dash and space
                    continue

            # Comment
            if char == "#":
                yield Token(
                    type=TokenType.COMMENT,
                    value=line[i:],  # Value is the entire comment string
                    line=line_num,
                    column=i,
                    indent_level=indent_level,
                )
                i = len(line)  # Consume rest of the line
                continue

            # Array/brace markers
            if char == "[":
                yield Token(
                    type=TokenType.ARRAY_START,
                    value="[",
                    line=line_num,
                    column=i,
                    indent_level=indent_level,
                )
                i += 1
                continue

            if char == "]":
                yield Token(
                    type=TokenType.ARRAY_END,
                    value="]",
                    line=line_num,
                    column=i,
                    indent_level=indent_level,
                )
                i += 1
                continue

            if char == "{":
                yield Token(
                    type=TokenType.BRACE_START,
                    value="{",
                    line=line_num,
                    column=i,
                    indent_level=indent_level,
                )
                i += 1
                continue

            if char == "}":
                yield Token(
                    type=TokenType.BRACE_END,
                    value="}",
                    line=line_num,
                    column=i,
                    indent_level=indent_level,
                )
                i += 1
                continue

            if char == "*":
                yield Token(
                    type=TokenType.STAR,
                    value="*",
                    line=line_num,
                    column=i,
                    indent_level=indent_level,
                )
                i += 1
                continue

            # Quoted string
            if char == '"':
                string_token, new_i = self._scan_quoted_string(line, i, line_num, indent_level)
                yield string_token
                i = new_i
                continue

            # Identifier or unquoted value
            token, new_i = self._scan_identifier(line, i, line_num, indent_level)
            yield token
            i = new_i

    def _scan_quoted_string(
        self, line: str, start: int, line_num: int, indent_level: int
    ) -> tuple[Token, int]:
        """Scan a quoted string.

        Args:
            line: Line content
            start: Start position (at opening quote)
            line_num: Line number
            indent_level: Indent level

        Returns:
            Tuple of (token, next_position)
        """
        i = start + 1  # Skip opening quote
        chars: list[str] = []

        while i < len(line):
            char = line[i]

            if char == "\\":
                # Escape sequence
                if i + 1 < len(line):
                    next_char = line[i + 1]
                    if next_char == "\\":
                        chars.append("\\")
                    elif next_char == '"':
                        chars.append('"')
                    elif next_char == "n":
                        chars.append("\n")
                    elif next_char == "r":
                        chars.append("\r")
                    elif next_char == "t":
                        chars.append("\t")
                    else:
                        msg = f"Invalid escape sequence: \\{next_char}"
                        raise ValueError(msg)
                    i += 2
                else:
                    msg = "Unterminated escape sequence"
                    raise ValueError(msg)

            elif char == '"':
                # End of string
                value = "".join(chars)
                return (
                    Token(
                        type=TokenType.QUOTED_STRING,
                        value=value,
                        line=line_num,
                        column=start,
                        indent_level=indent_level,
                    ),
                    i + 1,
                )
            else:
                chars.append(char)
                i += 1

        msg = f"Unterminated quoted string at line {line_num}"
        raise ValueError(msg)

    def _scan_identifier(
        self, line: str, start: int, line_num: int, indent_level: int
    ) -> tuple[Token, int]:
        """Scan an identifier or unquoted value.

        Args:
            line: Line content
            start: Start position
            line_num: Line number
            indent_level: Indent level

        Returns:
            Tuple of (token, next_position)
        """
        i = start
        chars: list[str] = []

        # Scan until delimiter or special character
        while i < len(line):
            char = line[i]
            if char in (":", ",", "[", "]", "{", "}", " ", "\t", "*"):
                break
            chars.append(char)
            i += 1

        value_str = "".join(chars)

        # Determine token type
        if value_str == "true":
            token_type = TokenType.BOOLEAN
            value: str | int | float | bool | None = True
        elif value_str == "false":
            token_type = TokenType.BOOLEAN
            value = False
        elif value_str == "null":
            token_type = TokenType.NULL
            value = None
        else:
            # Try to parse as number
            try:
                if "." in value_str:
                    value = float(value_str)
                    token_type = TokenType.NUMBER
                else:
                    value = int(value_str)
                    token_type = TokenType.NUMBER
            except ValueError:
                # It's an identifier/string
                token_type = TokenType.IDENTIFIER
                value = value_str

        return (
            Token(
                type=token_type,
                value=value,
                line=line_num,
                column=start,
                indent_level=indent_level,
            ),
            i,
        )
