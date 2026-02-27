"""Event-based parser for TOON v2.0 format.

Yields parsing events instead of full objects, allowing for true O(1) memory
usage even for deeply nested or massive objects.
"""

from collections import deque
from collections.abc import Iterator
from enum import Enum, auto
from typing import Any

from toonverter.decoders.lexer import Token, TokenType


class ParserEvent(Enum):
    """Types of parsing events yielded by ToonEventParser."""

    START_DOCUMENT = auto()
    END_DOCUMENT = auto()

    START_OBJECT = auto()
    END_OBJECT = auto()

    START_ARRAY = auto()
    END_ARRAY = auto()

    KEY = auto()
    VALUE = auto()


class ToonEventParser:
    """Incremental event-based parser for TOON format."""

    def __init__(self, tokens: Iterator[Token]) -> None:
        self.tokens = tokens
        self._buffer: deque[Token] = deque()

    def _peek_token(self, n: int = 0) -> Token | None:
        """Peek at the nth token ahead."""
        while len(self._buffer) <= n:
            try:
                self._buffer.append(next(self.tokens))
            except StopIteration:
                return None
        return self._buffer[n]

    def _next_token(self) -> Token | None:
        """Consume and return the next token."""
        if self._buffer:
            return self._buffer.popleft()
        try:
            return next(self.tokens)
        except StopIteration:
            return None

    def parse(self) -> Iterator[tuple[ParserEvent, Any]]:
        """Yield parsing events from the token stream."""
        yield (ParserEvent.START_DOCUMENT, None)

        # Skip initial newlines/comments
        while True:
            t = self._peek_token()
            if not t:
                break
            if t.type in (TokenType.NEWLINE, TokenType.COMMENT):
                self._next_token()
                continue
            break

        t = self._peek_token()
        if t:
            if t.type == TokenType.ARRAY_START:
                yield from self._parse_array()
            elif t.type == TokenType.BRACE_START:
                yield from self._parse_braced_object()
            else:
                # Root object detection
                is_obj = False
                if t.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
                    nt = self._peek_token(1)
                    if nt and nt.type in (TokenType.COLON, TokenType.ARRAY_START):
                        is_obj = True

                if is_obj:
                    yield from self._parse_indented_object(_root=True)
                else:
                    yield from self._parse_value()

        yield (ParserEvent.END_DOCUMENT, None)

    def _parse_value(self) -> Iterator[tuple[ParserEvent, Any]]:
        # Skip newlines/comments
        while True:
            t = self._peek_token()
            if not t:
                return
            if t.type in (TokenType.NEWLINE, TokenType.COMMENT):
                self._next_token()
                continue
            break

        t = self._peek_token()
        if not t:
            return

        if t.type == TokenType.ARRAY_START:
            yield from self._parse_array()
        elif t.type == TokenType.BRACE_START:
            yield from self._parse_braced_object()
        elif t.type == TokenType.INDENT:
            self._next_token()  # consume indent
            yield from self._parse_indented_object()
        else:
            # Check if this is the start of an inline/unbraced object
            # e.g., "key: value" inside a list item
            is_obj = False
            if t.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
                nt = self._peek_token(1)
                if nt and nt.type in (TokenType.COLON, TokenType.ARRAY_START):
                    is_obj = True

            if is_obj:
                yield from self._parse_indented_object()
            else:
                yield (ParserEvent.VALUE, t.value)
                self._next_token()

    def _parse_array(self) -> Iterator[tuple[ParserEvent, Any]]:
        self._next_token()  # [
        len_t = self._next_token()
        length = len_t.value if len_t else None

        # skip to :
        while True:
            t = self._next_token()
            if not t or t.type in (TokenType.COLON, TokenType.EOF):
                break

        yield (ParserEvent.START_ARRAY, length)

        while True:
            # Skip whitespace between items
            while True:
                t = self._peek_token()
                if not t:
                    break
                if t.type in (TokenType.NEWLINE, TokenType.INDENT, TokenType.COMMENT):
                    self._next_token()
                    continue
                break

            t = self._peek_token()
            if not t or t.type in (TokenType.DEDENT, TokenType.EOF, TokenType.ARRAY_END):
                if t and t.type == TokenType.DEDENT:
                    self._next_token()
                break

            if t.type == TokenType.DASH:
                self._next_token()  # consume -
                yield from self._parse_value()
            else:
                # Inline or tabular
                yield from self._parse_value()
                t = self._peek_token()
                if t and t.type == TokenType.COMMA:
                    self._next_token()

        yield (ParserEvent.END_ARRAY, None)

    def _parse_indented_object(self, *, _root: bool = False) -> Iterator[tuple[ParserEvent, Any]]:
        yield (ParserEvent.START_OBJECT, None)
        while True:
            # Skip whitespace between items
            while True:
                t = self._peek_token()
                if not t:
                    break
                if t.type in (TokenType.NEWLINE, TokenType.COMMENT):
                    self._next_token()
                    continue
                break

            t = self._peek_token()
            if not t or t.type == TokenType.EOF:
                break
            if t.type == TokenType.DEDENT:
                self._next_token()
                break
            if t.type == TokenType.DASH and not _root:
                break

            if t.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
                key = str(t.value)
                self._next_token()
                yield (ParserEvent.KEY, key)

                nt = self._peek_token()
                if nt and nt.type == TokenType.ARRAY_START:
                    yield from self._parse_array()
                else:
                    ct = self._next_token()
                    if not ct or ct.type != TokenType.COLON:
                        pass
                    yield from self._parse_value()
            else:
                self._next_token()

        yield (ParserEvent.END_OBJECT, None)

    def _parse_braced_object(self) -> Iterator[tuple[ParserEvent, Any]]:
        self._next_token()  # {
        yield (ParserEvent.START_OBJECT, None)
        while True:
            while True:
                t = self._peek_token()
                if not t:
                    break
                if t.type in (TokenType.NEWLINE, TokenType.COMMENT):
                    self._next_token()
                    continue
                break

            t = self._peek_token()
            if not t or t.type in (TokenType.BRACE_END, TokenType.EOF):
                if t and t.type == TokenType.BRACE_END:
                    self._next_token()
                break

            if t.type == TokenType.COMMA:
                self._next_token()
                continue

            if t.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
                key = str(t.value)
                self._next_token()
                yield (ParserEvent.KEY, key)

                ct = self._next_token()
                if ct and ct.type == TokenType.COLON:
                    yield from self._parse_value()
            else:
                self._next_token()
        yield (ParserEvent.END_OBJECT, None)
