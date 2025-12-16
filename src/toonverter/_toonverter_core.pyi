# src/toonverter/_toonverter_core.pyi
# Type stubs for the Rust _toonverter_core module.
# This file is used by MyPy and IDEs for static analysis.

from typing import Any

def decode_toon(text: str, indent_size: int | None = None) -> Any: ...
def encode_toon(obj: Any, indent_size: int | None = None, delimiter: str | None = None) -> str: ...

# Returns list of (path, content_or_error, is_error)
def convert_json_batch(
    paths: list[str], output_dir: str | None = None
) -> list[tuple[str, str, bool]]: ...

# Returns list of (path, content_or_error, is_error)
def convert_toon_batch(
    paths: list[str], output_dir: str | None = None
) -> list[tuple[str, str, bool]]: ...

# Returns list of (path, content_or_error, is_error)
def convert_json_directory(
    dir_path: str, recursive: bool = False, output_dir: str | None = None
) -> list[tuple[str, str, bool]]: ...
