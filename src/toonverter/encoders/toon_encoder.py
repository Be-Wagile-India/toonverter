"""Main TOON encoder implementing official v2.0 specification.

This is the primary encoder that orchestrates all encoding logic
according to the official TOON specification from github.com/toon-format/spec
"""

from typing import Any

from toonverter.core.config import (
    PARALLELISM_THRESHOLD,
    RECURSION_DEPTH_LIMIT,
    USE_RUST_ENCODER,
    rust_core,
)
from toonverter.core.exceptions import (
    EncodingError,
    InternalError,
    ProcessingError,
    ValidationError,
)
from toonverter.core.spec import ArrayForm, Delimiter, RootForm, ToonEncodeOptions, ToonValue
from toonverter.core.types import EncodeOptions

from .array_encoder import ArrayEncoder
from .indentation import IndentationManager
from .key_folding import KeyFolder
from .number_encoder import NumberEncoder
from .string_encoder import StringEncoder


# Avoid circular import at top level if possible, or handle carefully
try:
    from toonverter.optimization.engine import ContextOptimizer
except ImportError:
    ContextOptimizer = None  # type: ignore


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

        self._parallelism_threshold = (
            self.options.parallelism_threshold
            if self.options.parallelism_threshold is not None
            else PARALLELISM_THRESHOLD
        )

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
            # OPTIMIZATION HOOK:
            # If a token budget is set, run the ContextOptimizer first
            if self.options.token_budget and ContextOptimizer is not None:
                optimizer = ContextOptimizer(
                    budget=self.options.token_budget, policy=self.options.optimization_policy
                )
                data = optimizer.optimize(data)

            # Try Rust encoder if available and options allow
            # Rust encoder now supports custom indent and delimiter
            if (
                USE_RUST_ENCODER
                and self.options.key_folding == "none"
                and self.options.optimization_policy is None
            ):
                try:
                    return rust_core.encode_toon(
                        data,
                        indent_size=self.options.indent_size,
                        delimiter=self.options.delimiter.value,
                        recursion_depth_limit=RECURSION_DEPTH_LIMIT,
                    )
                except (ValidationError, ProcessingError, InternalError):
                    # Strict contract: Re-raise specific Rust errors
                    raise
                except ValueError as e:
                    # Fallback on error or raise?
                    # Since we want to rely on Rust if enabled, let's verify if it covers all cases.
                    # Currently Rust encoder is partial (simple/nested), might fail on complex tabular/list detection mismatch.
                    # Let's fallback to Python if Rust fails for now, or raise EncodingError.
                    msg = f"Failed to encode data (Rust): {e}"
                    raise EncodingError(msg) from e
                except Exception:
                    # Fallback to Python if unexpected error
                    pass

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

    def _encode_single_item(
        self, item_tuple: tuple[str, Any], depth: int, siblings: dict[str, Any] | None = None
    ) -> list[str]:
        key, value = item_tuple
        indent = self.indent_mgr.indent(depth)

        # Key folding logic
        # Pass siblings to allow proper collision detection
        context = siblings if siblings is not None else {key: value}
        if self.key_folder.should_fold_key(key, value, context):
            can_fold, key_chain = self.key_folder.can_fold_chain({key: value})
            if can_fold:
                folded_key = self.key_folder.fold_key_chain(key_chain)
                final_value = self.key_folder.get_folded_value({key: value}, key_chain)
                value_str = self._encode_value(final_value)
                return [f"{indent}{folded_key}: {value_str}"]

        # Regular key-value encoding
        if isinstance(value, dict):
            # Nested object
            if not value:
                return [f"{indent}{key}: {{}}"]
            return [f"{indent}{key}:", *self.encode_object(value, depth + 1)]
        if isinstance(value, list):
            # Array - detect form and encode
            if not value:
                return [f"{indent}{key}[0]:"]
            return self._encode_array(key, value, depth)

        # Primitive value
        value_str = self._encode_value(value)
        return [f"{indent}{key}: {value_str}"]

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

        # Sequential processing
        for item_tuple in obj.items():
            lines.extend(self._encode_single_item(item_tuple, depth, obj))

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


def _convert_options(options: EncodeOptions | ToonEncodeOptions | None) -> ToonEncodeOptions | None:
    """Convert EncodeOptions to ToonEncodeOptions if needed.

    Args:
        options: Either EncodeOptions (user-facing) or ToonEncodeOptions (internal)

    Returns:
        ToonEncodeOptions or None
    """
    if options is None:
        return None

    if isinstance(options, ToonEncodeOptions):
        return options

    # Convert EncodeOptions to ToonEncodeOptions
    # At this point, options MUST be an instance of EncodeOptions if the type hints are correct.
    # No need for 'if isinstance(options, EncodeOptions):' or 'else:'
    # Directly process options as EncodeOptions
    delimiter = Delimiter.from_string(options.delimiter)

    # Map compact mode to indent_size
    indent_size = 0 if options.compact else options.indent

    return ToonEncodeOptions(
        indent_size=indent_size,
        delimiter=delimiter,
        key_folding="none",  # EncodeOptions doesn't have key_folding
        strict=True,
        token_budget=options.token_budget,
        optimization_policy=options.optimization_policy,
    )


def encode(data: ToonValue, options: EncodeOptions | ToonEncodeOptions | None = None) -> str:
    """Convenience function to encode data to TOON format.

    Args:
        data: Data to encode
        options: Encoding options (EncodeOptions or ToonEncodeOptions)

    Returns:
        TOON-formatted string

    Examples:
        >>> encode({"name": "Alice", "age": 30})
        'name: Alice\\nage: 30'
    """
    toon_options = _convert_options(options)
    encoder = ToonEncoder(toon_options)
    return encoder.encode(data)
