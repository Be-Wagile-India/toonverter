"""Array encoding with three forms: inline, tabular, and list.

Implements the three array forms from TOON v2.0 specification:
1. Inline: key[N]: val1,val2,val3
2. Tabular: key[N]{field1,field2}:\n  row1\n  row2
3. List: key[N]:\n  - item1\n  - item2
"""

from typing import Any

from toonverter.core.spec import ArrayForm

from .indentation import IndentationManager
from .number_encoder import NumberEncoder
from .string_encoder import StringEncoder


class ArrayEncoder:
    """Encoder for arrays in TOON format.

    Supports three forms per TOON v2.0 spec:
    - Inline: for primitive arrays
    - Tabular: for uniform arrays of objects (most efficient)
    - List: for mixed/nested arrays
    """

    def __init__(
        self,
        string_encoder: StringEncoder,
        number_encoder: NumberEncoder,
        indent_mgr: IndentationManager,
    ) -> None:
        """Initialize array encoder.

        Args:
            string_encoder: String encoder for quoting
            number_encoder: Number encoder for canonical form
            indent_mgr: Indentation manager
        """
        self.str_enc = string_encoder
        self.num_enc = number_encoder
        self.indent_mgr = indent_mgr
        self.delimiter = string_encoder.delimiter

    def detect_array_form(self, arr: list[Any]) -> ArrayForm:
        """Detect which array form to use.

        Args:
            arr: Array to analyze

        Returns:
            ArrayForm (INLINE, TABULAR, or LIST)

        Examples:
            >>> encoder = ArrayEncoder(...)
            >>> encoder.detect_array_form([1, 2, 3])
            ArrayForm.INLINE
            >>> encoder.detect_array_form([{"id": 1}, {"id": 2}])
            ArrayForm.TABULAR
        """
        if not arr:
            return ArrayForm.INLINE

        is_inline = True
        is_tabular = True
        tabular_keys: tuple[str, ...] | None = None

        # Heuristic limit: scan at most 1000 items
        # If an array is huge, checking 1000 is enough to confidently detect format
        scan_limit = 1000
        items_to_scan = arr[:scan_limit]

        for i, item in enumerate(items_to_scan):
            # Check Primitive (for Inline)
            if is_inline:
                if not self._is_primitive(item):
                    is_inline = False

            # Check Dict & Uniform Keys & Primitive Values (for Tabular)
            if is_tabular:
                if not isinstance(item, dict):
                    is_tabular = False
                else:
                    # Check keys consistency
                    # Use tuple of sorted keys for stable comparison
                    current_keys = tuple(sorted(item.keys()))
                    if i == 0:
                        tabular_keys = current_keys
                    elif current_keys != tabular_keys:
                        is_tabular = False

                    # Check values are primitive (required for tabular)
                    if is_tabular:
                        for val in item.values():
                            if not self._is_primitive(val):
                                is_tabular = False
                                break

            # Early exit if both impossible
            if not is_inline and not is_tabular:
                return ArrayForm.LIST

        if is_inline:
            return ArrayForm.INLINE
        if is_tabular:
            return ArrayForm.TABULAR
        return ArrayForm.LIST

    def _is_primitive(self, val: Any) -> bool:
        """Check if value is a primitive type.

        Args:
            val: Value to check

        Returns:
            True if primitive (str, int, float, bool, None)
        """
        return isinstance(val, (str, int, float, bool, type(None)))

    def encode_inline(self, key: str, arr: list[Any], depth: int) -> str:
        """Encode inline array: key[N]: val1,val2,val3

        Args:
            key: Array key name
            arr: Array of primitives
            depth: Current indentation depth

        Returns:
            Single line string

        Examples:
            >>> encoder.encode_inline("tags", ["a", "b"], 0)
            'tags[2]: a,b'
        """
        indent = self.indent_mgr.indent(depth)
        length = len(arr)

        # Encode values
        encoded_vals = [self._encode_value(v) for v in arr]
        values_str = self.delimiter.join(encoded_vals)

        # Include delimiter in brackets if not comma (per TOON v2.0 spec)
        delimiter_marker = "" if self.delimiter == "," else self.delimiter
        return f"{indent}{key}[{length}{delimiter_marker}]: {values_str}"

    def encode_tabular(self, key: str, arr: list[dict[str, Any]], depth: int) -> list[str]:
        """Encode tabular array: key[N]{fields}:\n  rows...

        Args:
            key: Array key name
            arr: Array of dicts with uniform keys
            depth: Current indentation depth

        Returns:
            List of lines (header + data rows)

        Examples:
            >>> encoder.encode_tabular("users", [{"id": 1, "name": "Alice"}], 0)
            ['users[1]{id,name}:', '  1,Alice']
        """
        indent = self.indent_mgr.indent(depth)
        row_indent = self.indent_mgr.indent(depth + 1)

        length = len(arr)
        fields = list(arr[0].keys())

        # Header line: key[N]{field1,field2}: (with delimiter marker if not comma)
        delimiter_marker = "" if self.delimiter == "," else self.delimiter
        fields_str = self.delimiter.join(fields)
        header = f"{indent}{key}[{length}{delimiter_marker}]{{{fields_str}}}:"
        lines = [header]

        # Data rows
        for item in arr:
            values = [self._encode_value(item.get(field)) for field in fields]
            row = self.delimiter.join(values)
            lines.append(f"{row_indent}{row}")

        return lines

    def encode_list(self, key: str, arr: list[Any], depth: int, value_encoder: Any) -> list[str]:
        """Encode list array with - notation.

        Args:
            key: Array key name
            arr: Array of any values
            depth: Current indentation depth
            value_encoder: Encoder for complex values

        Returns:
            List of lines (header + list items)

        Examples:
            >>> encoder.encode_list("items", [1, "a", True], 0, ...)
            ['items[3]:', '  - 1', '  - a', '  - true']
        """
        indent = self.indent_mgr.indent(depth)
        item_indent = self.indent_mgr.indent(depth + 1)

        length = len(arr)
        header = f"{indent}{key}[{length}]:"

        lines = [header]

        for item in arr:
            if isinstance(item, dict):
                # Dict item - encode as nested object
                # Per TOON spec: first field on dash line, remaining fields at depth+2
                item_lines = value_encoder.encode_object(item, depth + 2)
                if item_lines:
                    # First line with "- " prefix at depth+1
                    # Strip leading whitespace from the first line since "- " provides the indentation
                    lines.append(f"{item_indent}- {item_lines[0].lstrip()}")
                    # Rest of lines already at depth+2 from encode_object
                    lines.extend(item_lines[1:])
            elif isinstance(item, list):
                # Nested array - encode recursively
                if not item:
                    # Empty array
                    lines.append(f"{item_indent}- [0]:")
                else:
                    # Detect form and encode nested array
                    nested_form = self.detect_array_form(item)
                    if nested_form == ArrayForm.INLINE:
                        # Inline nested array: - [3]: 1,2,3
                        nested_inline = self._encode_inline_values(item)
                        lines.append(f"{item_indent}- [{len(item)}]: {nested_inline}")
                    else:
                        # List or tabular form - needs full recursion
                        nested_lines = self._encode_nested_array_item(
                            item, depth + 1, value_encoder
                        )
                        lines.extend(nested_lines)
            else:
                # Primitive item
                encoded = self._encode_value(item)
                lines.append(f"{item_indent}- {encoded}")

        return lines

    def encode_root_array_inline(self, arr: list[Any]) -> str:
        """Encode root-level inline array.

        Args:
            arr: Array of primitives

        Returns:
            Single line string

        Examples:
            >>> encoder.encode_root_array_inline([1, 2, 3])
            '[3]: 1,2,3'
        """
        length = len(arr)
        encoded_vals = [self._encode_value(v) for v in arr]
        values_str = self.delimiter.join(encoded_vals)

        # Include delimiter in brackets if not comma (per TOON v2.0 spec)
        delimiter_marker = "" if self.delimiter == "," else self.delimiter
        return f"[{length}{delimiter_marker}]: {values_str}"

    def encode_root_array_tabular(self, arr: list[dict[str, Any]]) -> list[str]:
        """Encode root-level tabular array.

        Args:
            arr: Array of dicts with uniform keys

        Returns:
            List of lines

        Examples:
            >>> encoder.encode_root_array_tabular([{"id": 1}])
            ['[1]{id}:', '  1']
        """
        row_indent = self.indent_mgr.indent(1)
        length = len(arr)
        fields = list(arr[0].keys())

        # Header: [N]{fields}: (with delimiter marker if not comma)
        fields_str = self.delimiter.join(fields)
        delimiter_marker = "" if self.delimiter == "," else self.delimiter
        header = f"[{length}{delimiter_marker}]{{{fields_str}}}:"

        lines = [header]

        # Data rows
        for item in arr:
            values = [self._encode_value(item.get(field)) for field in fields]
            row = self.delimiter.join(values)
            lines.append(f"{row_indent}{row}")

        return lines

    def encode_root_array_list(self, arr: list[Any], value_encoder: Any) -> list[str]:
        """Encode root-level list array.

        Args:
            arr: Array of any values
            value_encoder: Encoder for complex values

        Returns:
            List of lines

        Examples:
            >>> encoder.encode_root_array_list([1, 2])
            ['[2]:', '  - 1', '  - 2']
        """
        item_indent = self.indent_mgr.indent(1)
        length = len(arr)
        header = f"[{length}]:"

        lines = [header]

        for item in arr:
            if isinstance(item, dict):
                item_lines = value_encoder.encode_object(item, 2)
                if item_lines:
                    lines.append(f"{item_indent}- {item_lines[0].lstrip()}")
                    lines.extend(item_lines[1:])
            else:
                encoded = self._encode_value(item)
                lines.append(f"{item_indent}- {encoded}")

        return lines

    def _encode_value(self, val: Any) -> str:
        """Encode a single value.

        Args:
            val: Value to encode

        Returns:
            Encoded string
        """
        if val is None:
            return "null"
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return self.num_enc.encode(val)
        if isinstance(val, str):
            return self.str_enc.encode(val)
        # Fallback: convert to string
        return self.str_enc.encode(str(val))

    def _encode_inline_values(self, arr: list[Any]) -> str:
        """Encode array values as inline comma-separated string.

        Args:
            arr: Array of primitives

        Returns:
            Comma-separated values string

        Examples:
            >>> encoder._encode_inline_values([1, 2, 3])
            '1,2,3'
        """
        encoded_values = [self._encode_value(val) for val in arr]
        return self.delimiter.join(encoded_values)

    def _encode_nested_array_item(
        self, arr: list[Any], depth: int, value_encoder: Any
    ) -> list[str]:
        """Encode nested array as list item.

        Args:
            arr: Nested array
            depth: Current depth
            value_encoder: Encoder for complex values

        Returns:
            List of lines for nested array

        Examples:
            >>> # For: - [2]:
            >>> #         - item1
            >>> #         - item2
        """
        item_indent = self.indent_mgr.indent(depth)
        nested_item_indent = self.indent_mgr.indent(depth + 1)

        header = f"{item_indent}- [{len(arr)}]:"
        lines = [header]

        for item in arr:
            if isinstance(item, dict):
                # Nested dict
                item_lines = value_encoder.encode_object(item, depth + 2)
                if item_lines:
                    lines.append(f"{nested_item_indent}- {item_lines[0].lstrip()}")
                    lines.extend(item_lines[1:])
            elif isinstance(item, list):
                # Double-nested array - recursion
                nested_nested_lines = self._encode_nested_array_item(item, depth + 1, value_encoder)
                lines.extend(nested_nested_lines)
            else:
                # Primitive
                encoded = self._encode_value(item)
                lines.append(f"{nested_item_indent}- {encoded}")

        return lines
