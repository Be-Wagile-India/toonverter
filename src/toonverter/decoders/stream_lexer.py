"""Streaming Lexer for TOON v2.0 format.

Tokenizes TOON input line-by-line using a generator approach for memory efficiency.
"""

from collections.abc import Iterator
from typing import TextIO

from toonverter.decoders.lexer import Token, TokenType, ToonLexer
from toonverter.encoders.indentation import detect_indentation


class StreamLexer:
    """Lexer for tokenizing TOON format streams.

    Converts TOON input stream into a generator of tokens.
    """

    def __init__(self, source: Iterator[str] | TextIO, indent_size: int = 2) -> None:
        """Initialize streaming lexer.

        Args:
            source: Iterator yielding lines of text (e.g. file object)
            indent_size: Number of spaces per indent level
        """
        self.source = source
        self.indent_size = indent_size
        self.current_line = 0
        self.current_indent = 0
        # Delegate line parsing to ToonLexer logic
        self._line_lexer = ToonLexer("")

    def tokenize(self) -> Iterator[Token]:
        """Yield tokens one by one."""
        self.current_indent = 0
        for line in self.source:
            # Handle potential trailing newlines from file reading
            line_content = line.rstrip("\n")

            # Skip empty lines (whitespace only)
            if not line_content.strip():
                self.current_line += 1
                continue

            # Handle indentation
            indent = detect_indentation(line_content)
            indent_level = indent // self.indent_size

            # Emit indent/dedent tokens
            if indent_level > self.current_indent:
                for _ in range(indent_level - self.current_indent):
                    yield Token(
                        type=TokenType.INDENT,
                        value=None,
                        line=self.current_line,
                        column=0,
                        indent_level=self.current_indent + 1,
                    )
                    self.current_indent += 1

            elif indent_level < self.current_indent:
                for _ in range(self.current_indent - indent_level):
                    yield Token(
                        type=TokenType.DEDENT,
                        value=None,
                        line=self.current_line,
                        column=0,
                        indent_level=self.current_indent - 1,
                    )
                    self.current_indent -= 1

            # Reuse ToonLexer's stateless line tokenization
            stripped = line_content.strip()
            if stripped == "-":
                stripped = "- "

            yield from self._line_lexer._tokenize_line(
                stripped, self.current_line, self.current_indent
            )

            # Add newline token
            yield Token(
                type=TokenType.NEWLINE,
                value=None,
                line=self.current_line,
                column=len(line_content),
                indent_level=self.current_indent,
            )

            self.current_line += 1

        # Add final dedents
        while self.current_indent > 0:
            self.current_indent -= 1
            yield Token(
                type=TokenType.DEDENT,
                value=None,
                line=self.current_line,
                column=0,
                indent_level=self.current_indent,
            )

        # Add EOF token
        yield Token(
            type=TokenType.EOF,
            value=None,
            line=self.current_line,
            column=0,
            indent_level=0,
        )
