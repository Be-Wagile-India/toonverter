import difflib
from typing import Any

from toonverter.core import DecodeOptions, registry  # Import necessary core utilities
from toonverter.core.exceptions import ConversionError
from toonverter.utils import read_file

from . import TiktokenCounter  # Import the existing token counter


class ToonDiffResult:
    """A structured report detailing differences between two data structures.

    This includes structural differences (what changed in the Python objects)
    and token differences (how the change impacts LLM consumption).
    """

    def __init__(
        self,
        identical: bool,
        token_diff: int,
        structural_diffs: dict[str, str],  # Key is path, value is description of change
        metadata: dict[str, Any],
    ) -> None:
        self.identical = identical
        self.token_diff = token_diff
        self.structural_diffs = structural_diffs
        self.metadata = metadata

    def summary(self) -> str:
        """Generates a human-readable summary of the differences."""
        diff_count = len(self.structural_diffs)
        summary = f"Comparison Result: {'Identical' if self.identical else 'DIFFERENT'}\n"
        summary += (
            f"- Structural Changes Found: {diff_count} item{'s' if diff_count != 1 else ''}\n"
        )
        summary += f"- Token Difference (A vs B): {self.token_diff} tokens ({'+' if self.token_diff > 0 else ''}{self.token_diff})"
        return summary

    def visualize(self, str_a: str, str_b: str, context_lines: int = 3) -> str:
        """Generates a unified diff (like 'git diff') of the serialized TOON strings."""
        lines_a = str_a.splitlines(keepends=True)
        lines_b = str_b.splitlines(keepends=True)

        # Use difflib to create a unified diff view
        diff_lines = difflib.unified_diff(
            lines_a,
            lines_b,
            fromfile="A_Original",
            tofile="B_Modified",
            lineterm="",
            n=context_lines,
        )
        return "".join(diff_lines)


class ToonDiffer:
    """Compares two data structures or their serialized strings."""

    def __init__(self, model: str = "gpt-4") -> None:
        """Initializes the differ with a token counter."""
        self.counter = TiktokenCounter(model=model)

    def diff_data(self, data_a: Any, data_b: Any) -> ToonDiffResult:
        """Compares two Python data structures."""
        # 1. Structural comparison
        structural_diffs = self._compare_structures(data_a, data_b)  # <--- Variable used below

        # 2. Token comparison (by encoding to a default format like 'toon')
        try:
            toon_adapter = registry.get("toon")
            str_a = toon_adapter.encode(data_a)
            str_b = toon_adapter.encode(data_b)
        except Exception as e:
            msg = f"Failed to encode data for comparison: {e}"
            raise ConversionError(msg)

        tokens_a = self.counter.count_tokens(str_a)
        tokens_b = self.counter.count_tokens(str_b)

        token_diff = tokens_b - tokens_a  # <--- Variable used below

        # The calculated variables MUST be consumed here by the return statement
        return ToonDiffResult(
            identical=not structural_diffs and (tokens_a == tokens_b),
            token_diff=token_diff,
            structural_diffs=structural_diffs,
            metadata={
                "format": "toon",
                "tokens_a": tokens_a,
                "tokens_b": tokens_b,
                "str_a": str_a,
                "str_b": str_b,
            },
        )

    def diff_files(
        self,
        file_a_path: str,
        file_b_path: str,
        format_a: str,
        format_b: str,
        **options: Any,
    ) -> ToonDiffResult:
        """Reads, decodes, and compares data from two files."""

        adapter_a = registry.get(format_a)
        adapter_b = registry.get(format_b)

        # Read files (synchronous reading is fine here, or use async_read_file if available)
        content_a = read_file(file_a_path)
        content_b = read_file(file_b_path)

        # Decode data
        decode_opts = DecodeOptions(**options) if options else None
        data_a = adapter_a.decode(content_a, decode_opts)
        data_b = adapter_b.decode(content_b, decode_opts)

        return self.diff_data(data_a, data_b)

    def _compare_structures(self, obj_a: Any, obj_b: Any, path: str = "") -> dict[str, str]:
        """Recursive function to find structural differences between two objects."""
        diffs = {}

        # Case 1: Simple comparison (equal or different simple types/values)
        if obj_a == obj_b:
            return diffs

        # Case 2: Dictionary comparison
        if isinstance(obj_a, dict) and isinstance(obj_b, dict):
            all_keys = set(obj_a.keys()) | set(obj_b.keys())
            for key in all_keys:
                new_path = f"{path}.{key}" if path else key

                if key not in obj_a:
                    diffs[new_path] = "Key added."
                elif key not in obj_b:
                    diffs[new_path] = "Key removed."
                else:
                    sub_diff = self._compare_structures(obj_a[key], obj_b[key], new_path)
                    diffs.update(sub_diff)

        # Case 3: List/Tuple comparison (basic check, could be more complex)
        elif isinstance(obj_a, (list, tuple)) and isinstance(obj_b, (list, tuple)):
            min_len = min(len(obj_a), len(obj_b))

            for i in range(min_len):
                new_path = f"{path}[{i}]"
                sub_diff = self._compare_structures(obj_a[i], obj_b[i], new_path)
                diffs.update(sub_diff)

            if len(obj_a) != len(obj_b):
                diffs[f"{path}.length"] = f"List length changed from {len(obj_a)} to {len(obj_b)}."

        # Case 4: Base case for differing values or types
        else:
            # Attempt to stringify for display, helpful for complex objects
            str_a = str(obj_a) if len(str(obj_a)) < 50 else f"{type(obj_a).__name__} object"
            str_b = str(obj_b) if len(str(obj_b)) < 50 else f"{type(obj_b).__name__} object"

            diffs[path or "root"] = f"Value changed/Type mismatch. A: '{str_a}' vs B: '{str_b}'"

        return diffs
