"""Official TOON v2.0 specification constants and types.

This module defines the core constants, types, and rules from the official
TOON specification at https://github.com/toon-format/spec
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal


# See note in types.py regarding imports
try:
    from toonverter.optimization.policy import OptimizationPolicy
except ImportError:
    OptimizationPolicy = Any  # type: ignore


# Spec version
TOON_SPEC_VERSION = "2.0"
TOON_SPEC_URL = "https://github.com/toon-format/spec"

# Indentation
DEFAULT_INDENT_SIZE = 2
INDENT_CHAR = " "  # Space only, tabs are forbidden for indentation


# Delimiters
class Delimiter(Enum):
    """Valid delimiters for arrays and fields."""

    COMMA = ","
    TAB = "\t"  # HTAB character
    PIPE = "|"

    @classmethod
    def from_string(cls, s: str) -> "Delimiter":
        """Parse delimiter from string."""
        if s == ",":
            return cls.COMMA
        if s == "\t":
            return cls.TAB
        if s == "|":
            return cls.PIPE
        msg = f"Invalid delimiter: {s!r}"
        raise ValueError(msg)

    def __str__(self) -> str:
        return self.value


DEFAULT_DELIMITER = Delimiter.COMMA


# Array forms
class ArrayForm(Enum):
    """Three forms of arrays in TOON."""

    INLINE = "inline"  # [N]: val1,val2,val3
    TABULAR = "tabular"  # [N]{field1,field2}:
    LIST = "list"  # [N]:\n  - item


# Root document forms
class RootForm(Enum):
    """Three possible root document structures."""

    OBJECT = "object"  # Default
    ARRAY = "array"  # Starts with array header
    PRIMITIVE = "primitive"  # Single value


# String quoting rules
RESERVED_WORDS = {"true", "false", "null"}

# Pattern for numbers that need quoting if they appear as strings
NUMBER_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$")

# Characters that require quoting
QUOTE_REQUIRED_CHARS = {
    " ",  # Space (internal whitespace)
    ":",  # Colon (key-value separator)
    '"',  # Double quote
    "\\",  # Backslash
    "[",  # Left bracket
    "]",  # Right bracket
    "{",  # Left brace
    "}",  # Right brace
    "\n",  # Newline
    "\r",  # Carriage return
    "\t",  # Tab
}

# Valid escape sequences (only these 5)
ESCAPE_SEQUENCES = {
    "\\": "\\",  # Backslash
    '"': '"',  # Double quote
    "n": "\n",  # Newline
    "r": "\r",  # Carriage return
    "t": "\t",  # Tab
}

# Reverse mapping for encoding
ESCAPE_CHARS = {
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}

# Key folding
KEY_SEGMENT_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
KEY_FOLD_SEPARATOR = "."


@dataclass
class ToonEncodeOptions:
    """Options for TOON encoding.

    Attributes:
        indent_size: Number of spaces per indentation level (default: 2)
        delimiter: Delimiter character for arrays and fields (default: comma)
        key_folding: Key folding mode - "safe" or "none" (default: "none")
        strict: Enable strict validation of output (default: True)
        token_budget: Maximum token count for output (active optimization)
        optimization_policy: Rules for intelligent degradation
    """

    indent_size: int = DEFAULT_INDENT_SIZE
    delimiter: Delimiter = DEFAULT_DELIMITER
    key_folding: Literal["safe", "none"] = "none"
    strict: bool = True
    token_budget: int | None = None
    optimization_policy: OptimizationPolicy | None = None
    parallelism_threshold: int | None = None

    def __post_init__(self) -> None:
        """Validate options."""
        if self.indent_size < 0:
            msg = "indent_size must be at least 0 (0 for compact mode)"
            raise ValueError(msg)
        if self.key_folding not in ("safe", "none"):
            msg = "key_folding must be 'safe' or 'none'"
            raise ValueError(msg)


@dataclass
class ToonDecodeOptions:
    """Options for TOON decoding.

    Attributes:
        strict: Enable strict validation of lengths and fields (default: True)
        type_inference: Automatically infer types from strings (default: True)
        indent_size: Number of spaces per indentation level (default: 2)
    """

    strict: bool = True
    type_inference: bool = True
    indent_size: int = DEFAULT_INDENT_SIZE


@dataclass
class ArrayHeader:
    """Parsed array header information.

    Represents the header line of an array: [length]{fields}:

    Attributes:
        length: Declared array length
        fields: Field names for tabular arrays (None for inline/list)
        delimiter: Delimiter used in this array
        form: Array form (inline, tabular, or list)
    """

    length: int
    fields: list[str] | None = None
    delimiter: Delimiter = DEFAULT_DELIMITER
    form: ArrayForm = ArrayForm.LIST

    def validate_row_count(self, actual_count: int) -> None:
        """Validate that row count matches declared length."""
        if self.length != actual_count:
            msg = f"Array length mismatch: declared {self.length}, got {actual_count}"
            raise ValueError(msg)

    def validate_field_count(self, actual_count: int) -> None:
        """Validate that field count matches row width."""
        if self.fields is not None and len(self.fields) != actual_count:
            msg = f"Field count mismatch: declared {len(self.fields)}, got {actual_count}"
            raise ValueError(msg)


@dataclass
class KeyPath:
    """Represents a potentially folded key path.

    For key folding: a.b.c represents {a: {b: {c: ...}}}

    Attributes:
        segments: List of key segments
        folded: Whether this path is folded (dotted notation)
    """

    segments: list[str]
    folded: bool = False

    @classmethod
    def parse(cls, key_string: str) -> "KeyPath":
        """Parse key string into segments."""
        if KEY_FOLD_SEPARATOR in key_string:
            segments = key_string.split(KEY_FOLD_SEPARATOR)
            # Validate all segments
            if all(KEY_SEGMENT_PATTERN.match(seg) for seg in segments):
                return cls(segments=segments, folded=True)
        return cls(segments=[key_string], folded=False)

    def to_string(self) -> str:
        """Convert back to string representation."""
        if self.folded:
            return KEY_FOLD_SEPARATOR.join(self.segments)
        return self.segments[0]

    def can_fold(self) -> bool:
        """Check if this path can be folded safely."""
        return len(self.segments) > 1 and all(
            KEY_SEGMENT_PATTERN.match(seg) for seg in self.segments
        )


# Type aliases for TOON data model (matches JSON)
ToonPrimitive = str | int | float | bool | None
ToonValue = ToonPrimitive | dict[str, "ToonValue"] | list["ToonValue"]
