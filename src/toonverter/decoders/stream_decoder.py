"""Streaming Decoder for TOON v2.0 format.

Decodes TOON input stream into Python objects iteratively.
"""

from collections import deque
from collections.abc import Iterator
from typing import Any

from toonverter.core.exceptions import DecodingError
from toonverter.core.spec import RootForm, ToonDecodeOptions
from toonverter.decoders.event_parser import ParserEvent, ToonEventParser
from toonverter.decoders.lexer import Token, TokenType
from toonverter.decoders.stream_lexer import StreamLexer
from toonverter.decoders.toon_decoder import ToonDecoder


class PeekableIterator:
    # ... (existing PeekableIterator implementation) ...

    def __init__(self, iterator: Iterator[Token]) -> None:
        self.iterator = iterator
        self.buffer: deque[Token] = deque()

    def __next__(self) -> Token:
        if self.buffer:
            return self.buffer.popleft()
        return next(self.iterator)

    def __iter__(self) -> Iterator[Token]:
        return self

    def peek(self, n: int = 0) -> Token | None:
        """Peek at the nth item ahead (0-based)."""
        while len(self.buffer) <= n:
            try:
                self.buffer.append(next(self.iterator))
            except StopIteration:
                return None
        return self.buffer[n]


class StreamDecoder:
    """Decoder for streaming TOON data.

    Features:
    - Iterative parsing of root arrays
    - Hybrid decoding: streams structure, parses values in chunks
    """

    def __init__(self, options: ToonDecodeOptions | None = None) -> None:
        self.options = options or ToonDecodeOptions()
        self.chunk_decoder = ToonDecoder(self.options)

    def items(self, stream: Iterator[str], events: bool = False) -> Iterator[Any]:
        """Yield items from a root array one by one.

        Args:
            stream: Iterator of TOON lines.
            events: If True, yield (ParserEvent, value) pairs instead of full objects.
                    This is the most memory-efficient mode.

        Yields:
            Decoded items or parsing events.
        """
        lexer = StreamLexer(stream, indent_size=self.options.indent_size)
        parser = ToonEventParser(lexer.tokenize())

        parser_events = parser.parse()

        try:
            # Skip START_DOCUMENT
            ev, _ = next(parser_events)

            # Root must be START_ARRAY for item-by-item streaming
            ev, val = next(parser_events)
            if ev == ParserEvent.START_ARRAY:
                if events:
                    yield (ev, val)
                    yield from parser_events
                else:
                    yield from self._yield_full_items(parser_events)
            elif ev == ParserEvent.VALUE:
                # Root primitive
                yield val
            elif ev == ParserEvent.START_OBJECT:
                # Root object - yield as single item if not in events mode
                if events:
                    yield (ev, val)
                    yield from parser_events
                else:
                    # Reconstruct full root object
                    yield self._reconstruct_item(ev, val, parser_events)
        except StopIteration:
            pass

    def _yield_full_items(self, events: Iterator[tuple[ParserEvent, Any]]) -> Iterator[Any]:
        """Reconstruct top-level items from events."""
        for event, value in events:
            if event == ParserEvent.END_ARRAY:
                break

            # Reconstruct one full item
            item = self._reconstruct_item(event, value, events)
            yield item

    def _reconstruct_item(
        self, first_event: ParserEvent, first_value: Any, events: Iterator[tuple[ParserEvent, Any]]
    ) -> Any:
        """Helper to reconstruct a single complex item from event stream."""
        if first_event == ParserEvent.VALUE:
            return first_value

        stack: list[Any] = []
        current_key: str | None = None

        # Initialize stack with first container
        if first_event == ParserEvent.START_OBJECT:
            stack.append({})
        elif first_event == ParserEvent.START_ARRAY:
            stack.append([])
        else:
            return first_value  # Should not happen for KEY/VALUE

        for event, value in events:
            if event == ParserEvent.START_OBJECT:
                stack.append({})
            elif event == ParserEvent.START_ARRAY:
                stack.append([])
            elif event == ParserEvent.KEY:
                current_key = value
            elif event == ParserEvent.VALUE:
                target = stack[-1]
                if isinstance(target, dict):
                    if current_key is None:
                        # Should not happen in valid TOON, but for robustness:
                        continue
                    target[current_key] = value
                    current_key = None
                else:
                    target.append(value)
            elif event in (ParserEvent.END_OBJECT, ParserEvent.END_ARRAY):
                finished = stack.pop()
                if not stack:
                    return finished

                target = stack[-1]
                if isinstance(target, dict):
                    if current_key is not None:
                        target[current_key] = finished
                        current_key = None
                else:
                    target.append(finished)

        # If we reach here, doc ended prematurely
        return stack[0] if stack else None

    def decode_stream(self, stream: Iterator[str]) -> Iterator[Any]:
        """Decode a stream of TOON lines.

        Assumes the root is an Array. Yields decoded items one by one.
        """
        lexer = StreamLexer(stream)
        tokens = PeekableIterator(lexer.tokenize())

        # Skip initial structural tokens
        while True:
            token = tokens.peek()
            if not token:
                return
            if token.type in (TokenType.NEWLINE, TokenType.INDENT):
                next(tokens)
                continue
            break

        first = tokens.peek()
        if not first or first.type == TokenType.EOF:
            return

        # We strictly support streaming for Root Arrays [N]:
        if first.type == TokenType.ARRAY_START:
            yield from self._parse_stream_array(tokens)
        else:
            # Fallback: Collect all remaining tokens and parse using root logic
            # This allows the API to be consistent for small objects
            all_tokens = list(tokens)
            self.chunk_decoder.tokens = all_tokens
            self.chunk_decoder.pos = 0

            root_form = self.chunk_decoder._detect_root_form()
            if root_form == RootForm.ARRAY:
                # Should have been caught, but safe fallback
                yield self.chunk_decoder._parse_root_array()
            elif root_form == RootForm.PRIMITIVE:
                yield self.chunk_decoder._parse_root_primitive()
            else:
                yield self.chunk_decoder._parse_root_object()

    def _parse_stream_array(self, tokens: PeekableIterator) -> Iterator[Any]:
        """Parse root array tokens and yield items."""
        # 1. Header: [
        next(tokens)

        # 2. Length
        length_token = next(tokens)
        length: int | None = None
        if length_token.type == TokenType.NUMBER:
            length = int(length_token.value)  # type: ignore
        elif length_token.type == TokenType.STAR:
            length = None
        else:
            # Maybe empty array []?
            # If ARRAY_END comes next
            if length_token.type == TokenType.ARRAY_END:
                return  # Empty array
            msg = "Expected array length or '*'"
            raise DecodingError(msg)

        # 3. Skip to Colon (handling fields/delimiters)
        while True:
            t = next(tokens)
            if t.type == TokenType.COLON:
                break
            if t.type == TokenType.EOF:
                return  # Malformed or done

        # 4. Parse Items
        items_yielded = 0

        while length is None or items_yielded < length:
            t_peeked = tokens.peek()
            if t_peeked is None or t_peeked.type == TokenType.EOF:
                break

            # Skip structural
            if t_peeked.type in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
                next(tokens)
                continue

            # List Item Marker
            if t_peeked.type == TokenType.DASH:
                _ = next(tokens)  # Consume '-'

                # Capture value tokens
                val_tokens = self._collect_value_tokens(tokens)
                if val_tokens:
                    item = self._decode_chunk(val_tokens)
                    yield item
                    items_yielded += 1

            # Inline Item (no dash)
            else:
                # Primitive or inline object in inline array
                val_tokens = self._collect_value_tokens(tokens)
                if val_tokens:
                    item = self._decode_chunk(val_tokens)
                    yield item
                    items_yielded += 1

                # Skip comma
                nxt = tokens.peek()
                if nxt and nxt.type == TokenType.COMMA:
                    next(tokens)

    def _collect_value_tokens(self, tokens: PeekableIterator) -> list[Token]:
        """Collect tokens for a single value."""
        collected: list[Token] = []
        balance = 0  # Brackets

        # We need to detect if we are entering a multiline block (indentation)
        first = tokens.peek()
        if not first:
            return []

        # Identify base indentation level.
        # If we are at 'name: Alice' inside a list item, the indentation is that of 'name'.
        # BUT tokens have absolute indent level.
        start_indent = first.indent_level

        while True:
            t = tokens.peek()
            if t is None or t.type == TokenType.EOF:
                break

            # Stop conditions
            if balance == 0:
                if t.type == TokenType.DASH:
                    break  # Next item

                # DEDENT check: Stop when dedenting below start indent (end of block).
                if t.type == TokenType.DEDENT and t.indent_level < start_indent:
                    break

                # Inline array item separator
                if t.type == TokenType.COMMA:
                    break

                # Newline handling for primitives
                if t.type == TokenType.NEWLINE:
                    # Peek further
                    next_t = tokens.peek(1)
                    # If next line is NOT indented relative to current item, we are done.
                    # (Unless inside brackets)
                    if next_t and next_t.indent_level <= start_indent:
                        # End of value. Consume newline.
                        collected.append(next(tokens))
                        break

            # Consume
            curr = next(tokens)
            collected.append(curr)

            if curr.type in (TokenType.ARRAY_START, TokenType.BRACE_START):
                balance += 1
            elif curr.type in (TokenType.ARRAY_END, TokenType.BRACE_END):
                balance -= 1

        return collected

    def _decode_chunk(self, tokens: list[Token]) -> Any:
        """Decode a list of tokens using standard decoder."""
        self.chunk_decoder.tokens = tokens
        self.chunk_decoder.pos = 0

        # Find the first content token to determine base depth
        start = 0
        while start < len(tokens) and tokens[start].type in (TokenType.NEWLINE, TokenType.INDENT):
            start += 1

        if start >= len(tokens):
            # Just whitespace/newlines? Return None?
            return None

        # Use _parse_value(depth=0) to dispatch to correct parsing method
        return self.chunk_decoder._parse_value(depth=0)
