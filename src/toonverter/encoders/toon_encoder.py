"""Main TOON encoder implementing official v2.0 specification.

This is the primary encoder that orchestrates all encoding logic
according to the official TOON specification from github.com/toon-format/spec
"""

from typing import Any

from toonverter.core.exceptions import EncodingError, ValidationError
from toonverter.core.spec import ArrayForm, RootForm, ToonEncodeOptions, ToonValue

from .array_encoder import ArrayEncoder
from .indentation import IndentationManager
from .key_folding import KeyFolder
from .number_encoder import NumberEncoder
from .string_encoder import StringEncoder


class ToonEncoder:
    """Official TOON v2.0 encoder.

    Encodes Python data structures to TOON format following the official
    specification with support for:
    - Indentation-based objects (YAML-like)
    - Three array forms (inline, tabular, list)
    - Minimal quoting
    - Canonical numbers
    - Optional key folding
    """

    def __init__(self, options: ToonEncodeOptions | None = None) -> None:
        """Initialize TOON encoder.

        Args:
            options: Encoding options (uses defaults if None)
        """
        self.options = options or ToonEncodeOptions()

        # Initialize sub-encoders
        self.str_enc = StringEncoder(self.options.delimiter)
        self.num_enc = NumberEncoder()
        self.indent_mgr = IndentationManager(self.options.indent_size)
        self.array_enc = ArrayEncoder(self.str_enc, self.num_enc, self.indent_mgr)
        self.key_folder = KeyFolder(enabled=self.options.key_folding == "safe")

    def encode(self, data: ToonValue) -> str:
        """Encode Python data to TOON format.

        Args:
            data: Data to encode (dict, list, or primitive)

        Returns:
            TOON-formatted string

        Raises:
            EncodingError: If encoding fails
            ValidationError: If data contains unsupported types

        Examples:
            >>> encoder = ToonEncoder()
            >>> encoder.encode({"name": "Alice", "age": 30})
            'name: Alice\\nage: 30'
        """
        try:
            return self._encode_root(data)
        except (TypeError, ValueError, RecursionError) as e:
            msg = f"Failed to encode data: {e}"
            raise EncodingError(msg) from e

    def _encode_root(self, data: ToonValue) -> str:
        """Encode root-level data.

        Args:
            data: Root data

        Returns:
            TOON string
        """
        root_form = self._detect_root_form(data)

        if root_form == RootForm.PRIMITIVE:
            # Single primitive value
            return self._encode_value(data)

        if root_form == RootForm.ARRAY:
            # Root-level array
            assert isinstance(data, list)
            return self._encode_root_array(data)

        # RootForm.OBJECT
        # Root-level object (default)
        assert isinstance(data, dict)
        lines = self.encode_object(data, depth=0)
        return "\n".join(lines)

    def _detect_root_form(self, data: ToonValue) -> RootForm:
        """Detect the form of root data.

        Args:
            data: Root data

        Returns:
            RootForm enum value
        """
        if isinstance(data, dict):
            return RootForm.OBJECT
        if isinstance(data, list):
            return RootForm.ARRAY
        # Primitive
        return RootForm.PRIMITIVE

    def _encode_root_array(self, arr: list[Any]) -> str:
        """Encode root-level array.

        Args:
            arr: Array data

        Returns:
            TOON string
        """
        if not arr:
            return "[0]:"

        form = self.array_enc.detect_array_form(arr)

        if form == ArrayForm.INLINE:
            return self.array_enc.encode_root_array_inline(arr)
        if form == ArrayForm.TABULAR:
            lines = self.array_enc.encode_root_array_tabular(arr)
            return "\n".join(lines)
        # ArrayForm.LIST
        lines = self.array_enc.encode_root_array_list(arr, self)
        return "\n".join(lines)

    def encode_object(self, obj: dict[str, Any], depth: int) -> list[str]:
        """Encode object with indentation.

        Args:
            obj: Dictionary to encode
            depth: Current indentation depth

        Returns:
            List of lines

        Examples:
            >>> encoder = ToonEncoder()
            >>> encoder.encode_object({"name": "Alice"}, 0)
            ['name: Alice']
        """
        if not obj:
            return []

        lines: list[str] = []
        indent = self.indent_mgr.indent(depth)

        # Process each key-value pair
        for key, value in obj.items():
            # Check if this key can be folded
            if self.key_folder.should_fold_key(key, value, obj):
                can_fold, key_chain = self.key_folder.can_fold_chain({key: value})
                if can_fold:
                    folded_key = self.key_folder.fold_key_chain(key_chain)
                    final_value = self.key_folder.get_folded_value({key: value}, key_chain)
                    # Encode as single line
                    value_str = self._encode_value(final_value)
                    lines.append(f"{indent}{folded_key}: {value_str}")
                    continue

            # Regular key-value encoding
            if isinstance(value, dict):
                # Nested object
                lines.append(f"{indent}{key}:")
                nested_lines = self.encode_object(value, depth + 1)
                lines.extend(nested_lines)

            elif isinstance(value, list):
                # Array - detect form and encode
                if not value:
                    lines.append(f"{indent}{key}[0]:")
                else:
                    array_lines = self._encode_array(key, value, depth)
                    lines.extend(array_lines)

            else:
                # Primitive value
                value_str = self._encode_value(value)
                lines.append(f"{indent}{key}: {value_str}")

        return lines

    def _encode_array(self, key: str, arr: list[Any], depth: int) -> list[str]:
        """Encode array with key.

        Args:
            key: Array key
            arr: Array data
            depth: Current depth

        Returns:
            List of lines
        """
        form = self.array_enc.detect_array_form(arr)

        if form == ArrayForm.INLINE:
            line = self.array_enc.encode_inline(key, arr, depth)
            return [line]
        if form == ArrayForm.TABULAR:
            return self.array_enc.encode_tabular(key, arr, depth)
        # ArrayForm.LIST
        return self.array_enc.encode_list(key, arr, depth, self)

    def _encode_value(self, val: Any) -> str:
        """Encode a single value (primitive).

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
        msg = f"Unsupported type for TOON encoding: {type(val).__name__}"
        raise ValidationError(msg)


def encode(data: ToonValue, options: ToonEncodeOptions | None = None) -> str:
    """Convenience function to encode data to TOON format.

    Args:
        data: Data to encode
        options: Encoding options

    Returns:
        TOON-formatted string

    Examples:
        >>> encode({"name": "Alice", "age": 30})
        'name: Alice\\nage: 30'
    """
    encoder = ToonEncoder(options)
    return encoder.encode(data)
