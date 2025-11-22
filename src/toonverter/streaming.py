import csv
import io
import re
from collections.abc import Generator, Iterable, Sized
from typing import Any, TextIO


# Regex Patterns for TOON v2.0 Parsing
# Regex for simple key-value pairs
RE_KV = re.compile(r"^(\s*)([\w\-\.]+):\s*(.+)?$")
# Regex for Table Array Start like "key[3]{...}:"
RE_TABLE_START = re.compile(r"^(\s*)([\w\-\.]+)\[(\d+)\]\{([^}]+)\}:\s*$")


class StreamingEncoder:
    """Writes TOON data incrementally to a stream."""

    def __init__(
        self,
        stream: TextIO,
        indent_char: str = " ",
        indent_size: int = 2,
    ) -> None:
        self.stream = stream
        self.indent_char = indent_char
        self.indent_size = indent_size

    def _indent(self, level: int) -> str:
        return self.indent_char * (level * self.indent_size)

    def write_kv(self, key: str, value: Any, level: int = 0) -> None:
        """Write a simple key-value pair (e.g., 'name: Alice')."""
        # Basic value sanitization
        val_str = str(value).replace("\n", "\\n")
        self.stream.write(f"{self._indent(level)}{key}: {val_str}\n")

    def write_section_start(self, key: str, level: int = 0) -> None:
        """Start a nested object section (e.g., 'address:')."""
        self.stream.write(f"{self._indent(level)}{key}:\n")

    def write_table_header(self, key: str, count: int, headers: list[str], level: int = 0) -> None:
        """
        Write the header for a tabular array.
        Output: key[N]{col1,col2}:
        """
        header_str = ",".join(headers)
        self.stream.write(f"{self._indent(level)}{key}[{count}]{{{header_str}}}:\n")

    def write_table_row(self, values: list[Any], level: int = 0) -> None:
        """Write a single CSV-style row for a table."""
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="")
        writer.writerow(values)
        row_str = buffer.getvalue()

        self.stream.write(f"{self._indent(level)}{row_str}\n")

    def dump_iterable(
        self,
        key: str,
        data: Iterable[dict[str, Any]],
        headers: list[str] | None = None,
        level: int = 0,
    ) -> None:
        """
        Stream an entire list of dicts as a TOON table.

        Handles the [N] counting requirement by converting generators to lists
        if they do not implement __len__.
        """
        items: list[dict[str, Any]] | Iterable[dict[str, Any]]
        length: int

        # 1. Resolve Data & Length
        if isinstance(data, Sized):
            length = len(data)
            items = data
        else:
            # Must consume generator to get length for TOON spec compliance
            items = list(data)
            length = len(items)

        if length == 0:
            return

        # 2. Infer Headers if not provided
        if not headers:
            if isinstance(items, list) and len(items) > 0:
                headers = list(items[0].keys())

        if not headers:
            # Fallback: If we can't infer headers, we cannot write a table.
            return

        # 3. Stream Output
        self.write_table_header(key, length, headers, level)

        for item in items:
            row_values = [item.get(h, "") for h in headers]
            self.write_table_row(row_values, level + 1)


class StreamingDecoder:
    """Parses a TOON stream line-by-line and yields structured events or objects."""

    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def iter_items(
        self,
    ) -> Generator[tuple[str, str | dict[str, Any]], None, None]:
        """
        Yields (path, value) tuples.

        Returns:
            Generator yielding:
            - (key, value_string) for simple pairs
            - (key, dict) for table rows
        """
        # Stack stores: (indent_level, key_name)
        context_stack: list[tuple[int, str]] = []

        # Table mode stores: {indent, headers, key}
        table_info: dict[str, Any] | None = None

        for line in self.stream:
            raw_line = line.rstrip()
            if not raw_line:
                continue

            # Calculate indentation
            indent_len = len(raw_line) - len(raw_line.lstrip())
            content = raw_line.strip()

            # --- 1. Handle Table Mode (Inside an Array) ---
            if table_info:
                if indent_len <= table_info["indent"]:
                    # Indentation dropped -> Table ended
                    table_info = None
                else:
                    # Process Row using csv module
                    row_values = self._parse_csv_row(content)

                    # Map headers to values
                    headers = table_info["headers"]
                    row_dict = dict(zip(headers, row_values, strict=False))

                    yield (table_info["key"], row_dict)
                    continue

            # --- 2. Manage Stack (Context) ---
            while context_stack and context_stack[-1][0] >= indent_len:
                context_stack.pop()

            # --- 3. Parse Line Types ---

            # Case A: Table Header -> "users[5]{id,name}:"
            table_match = RE_TABLE_START.match(raw_line)
            if table_match:
                _, key, _count, headers_str = table_match.groups()
                headers = [h.strip() for h in headers_str.split(",")]

                table_info = {
                    "indent": indent_len,
                    "headers": headers,
                    "key": key,
                }
                context_stack.append((indent_len, key))
                continue

            # Case B: Nested Object Start -> "address:"
            if content.endswith(":") and not content.startswith("{") and "[" not in content:
                key = content[:-1]
                context_stack.append((indent_len, key))
                continue

            # Case C: Simple Key-Value -> "city: NYC"
            kv_match = RE_KV.match(raw_line)
            if kv_match:
                _, key, val = kv_match.groups()
                yield (key, val)

    def _parse_csv_row(self, line: str) -> list[str]:
        """Parse a single CSV line using the standard library."""
        reader = csv.reader([line])
        for row in reader:
            return row
        return []


# --- Facade Functions ---


def stream_dump(data: Iterable[dict[str, Any]], stream: TextIO, key: str = "data") -> None:
    """Helper to dump a list of dicts directly to a stream."""
    encoder = StreamingEncoder(stream)
    encoder.dump_iterable(key, data)


def stream_load(stream: TextIO) -> Generator[dict[str, Any], None, None]:
    """
    Helper that assumes the stream contains a list of items (Table Mode).
    Yields items one by one.
    """
    decoder = StreamingDecoder(stream)
    for _, val in decoder.iter_items():
        if isinstance(val, dict):
            yield val
