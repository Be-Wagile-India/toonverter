"""Streaming TOON encoder implementing advanced iterative generator pattern.

This encoder provides memory-efficient streaming encoding for large datasets,
avoiding recursion limits and memory overhead of building full strings.
"""

import io
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from toonverter.core.exceptions import EncodingError
from toonverter.core.spec import ToonEncodeOptions, ToonValue
from toonverter.encoders.indentation import IndentationManager
from toonverter.encoders.number_encoder import NumberEncoder
from toonverter.encoders.string_encoder import StringEncoder


@dataclass
class StreamList:
    """Helper class for streaming iterators with known length."""

    iterator: Iterator[Any]
    length: int


class ContextType(Enum):
    """Type of current encoding context."""

    DICT = auto()
    LIST = auto()


@dataclass
class EncoderContext:
    """State context for the iterative encoder."""

    type: ContextType
    iterator: Iterator[Any]
    depth: int
    is_first: bool = True

    # For Lists, we need to know if we are in a Root Array List form or nested
    is_root_array: bool = False


class ToonStreamEncoder:
    """Advanced Iterative Streaming Encoder for TOON format.

    Features:
    - O(1) Memory usage (generator-based)
    - Stack-based iteration (unlimited depth, no RecursionError)
    - Lazy array processing
    """

    def __init__(self, options: ToonEncodeOptions | None = None) -> None:
        self.options = options or ToonEncodeOptions()
        self.str_enc = StringEncoder(self.options.delimiter)
        self.num_enc = NumberEncoder()
        self.indent_mgr = IndentationManager(self.options.indent_size)

    def iterencode(self, data: ToonValue | StreamList) -> Iterator[str]:
        """Encode data to TOON format as a stream of strings.

        Args:
            data: Data to encode

        Yields:
            Chunks of the encoded string.
        """
        try:
            # 1. Root Primitive (excluding StreamList)
            if not isinstance(data, StreamList) and self._is_primitive(data):
                yield self._encode_value(data)
                return

            stack: deque[EncoderContext] = deque()

            # 2. Initialize Root Context
            if isinstance(data, dict):
                if not data:
                    yield ""  # Empty dict -> empty string
                    return

                stack.append(
                    EncoderContext(type=ContextType.DICT, iterator=iter(data.items()), depth=0)
                )

            elif isinstance(data, list):
                if not data:
                    yield "[0]:"
                    return

                # Default to LIST form for streaming root arrays
                yield f"[{len(data)}]:\n"
                first_yield = False

                stack.append(
                    EncoderContext(
                        type=ContextType.LIST, iterator=iter(data), depth=0, is_root_array=True
                    )
                )
            elif isinstance(data, StreamList):
                if data.length == 0:
                    yield "[0]:"
                    return

                yield f"[{data.length}]:\n"
                first_yield = False

                stack.append(
                    EncoderContext(
                        type=ContextType.LIST, iterator=data.iterator, depth=0, is_root_array=True
                    )
                )

            else:
                msg = f"Unsupported root type: {type(data)}"
                raise EncodingError(msg)

            # 3. Process Stack
            # We maintain a 'pending_newline' state to strictly emulate "\n".join()
            # The first line yielded never has a prefix \n.
            # All subsequent lines get a prefix \n.
            first_yield = True

            while stack:
                ctx = stack[-1]

                try:
                    if ctx.type == ContextType.DICT:
                        key, value = next(ctx.iterator)

                        # Prepare prefix
                        prefix = "" if first_yield else "\n"
                        indent = self.indent_mgr.indent(ctx.depth)

                        if isinstance(value, dict):
                            yield f"{prefix}{indent}{key}:"
                            first_yield = False

                            if value:
                                stack.append(
                                    EncoderContext(
                                        type=ContextType.DICT,
                                        iterator=iter(value.items()),
                                        depth=ctx.depth + 1,
                                    )
                                )

                        elif isinstance(value, list):
                            yield f"{prefix}{indent}{key}:"
                            first_yield = False

                            if not value:
                                yield f"\n{self.indent_mgr.indent(ctx.depth + 1)}[0]:"
                            else:
                                # Start array header
                                yield f"\n{self.indent_mgr.indent(ctx.depth + 1)}[{len(value)}]:\n"
                                stack.append(
                                    EncoderContext(
                                        type=ContextType.LIST,
                                        iterator=iter(value),
                                        depth=ctx.depth + 1,
                                    )
                                )
                        elif isinstance(value, StreamList):
                            yield f"{prefix}{indent}{key}:"
                            first_yield = False

                            if value.length == 0:
                                yield f"\n{self.indent_mgr.indent(ctx.depth + 1)}[0]:"
                            else:
                                yield f"\n{self.indent_mgr.indent(ctx.depth + 1)}[{value.length}]:\n"
                                stack.append(
                                    EncoderContext(
                                        type=ContextType.LIST,
                                        iterator=value.iterator,
                                        depth=ctx.depth + 1,
                                    )
                                )

                        else:
                            # Primitive
                            val_str = self._encode_value(value)
                            yield f"{prefix}{indent}{key}: {val_str}"
                            first_yield = False

                    elif ctx.type == ContextType.LIST:
                        item = next(ctx.iterator)

                        prefix = "" if first_yield else "\n"
                        indent = self.indent_mgr.indent(ctx.depth)

                        if isinstance(item, dict):
                            # Object in list
                            yield f"{prefix}{indent}-"
                            first_yield = False

                            if item:
                                stack.append(
                                    EncoderContext(
                                        type=ContextType.DICT,
                                        iterator=iter(item.items()),
                                        depth=ctx.depth + 1,
                                    )
                                )

                        elif isinstance(item, list):
                            # List in list
                            yield f"{prefix}{indent}-"
                            first_yield = False
                            if item:
                                # Header for inner list
                                yield f" [{len(item)}]:"

                                stack.append(
                                    EncoderContext(
                                        type=ContextType.LIST,
                                        iterator=iter(item),
                                        depth=ctx.depth + 1,
                                    )
                                )
                            else:
                                yield " [0]:"

                        elif isinstance(item, StreamList):
                            # Nested StreamList
                            yield f"{prefix}{indent}-"
                            first_yield = False
                            if item.length > 0:
                                yield f" [{item.length}]:"
                                stack.append(
                                    EncoderContext(
                                        type=ContextType.LIST,
                                        iterator=item.iterator,
                                        depth=ctx.depth + 1,
                                    )
                                )
                            else:
                                yield " [0]:"

                        else:
                            # Primitive in list
                            val_str = self._encode_value(item)
                            yield f"{prefix}{indent}- {val_str}"
                            first_yield = False

                except StopIteration:
                    stack.pop()

        except Exception as e:
            msg = f"Streaming encoding failed: {e}"
            raise EncodingError(msg) from e

    def _is_primitive(self, data: Any) -> bool:
        return not isinstance(data, (dict, list, StreamList))

    def _encode_value(self, val: Any) -> str:
        """Encode single primitive."""
        if val is None:
            return "null"
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return self.num_enc.encode(val)
        if isinstance(val, str):
            return self.str_enc.encode(val)
        msg = f"Unsupported type: {type(val)}"
        raise EncodingError(msg)

    def stream_encode(self, data: ToonValue | StreamList, output_stream: io.TextIOBase) -> None:
        """Encode data to TOON format and write directly to a text stream.

        This method avoids building the entire output string in memory, making it suitable
        for extremely large outputs.

        Args:
            data: Data to encode (dict, list, primitive, or StreamList).
            output_stream: A `io.TextIOBase` object to which the encoded TOON string
                           will be written.
        Raises:
            EncodingError: If streaming encoding fails.
        """
        try:
            for chunk in self.iterencode(data):
                output_stream.write(chunk)
        except EncodingError:
            raise
        except Exception as e:
            msg = f"Failed to write streamed TOON output: {e}"
            raise EncodingError(msg) from e
