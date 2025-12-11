"""Configuration settings for Toonverter."""

import os
import sys
import warnings
from pathlib import Path
from types import ModuleType
from typing import Any


# Handle TOML parser import (tomllib for Python 3.11+, tomli backport otherwise)
tomllib: ModuleType | None
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# Try to import the Rust-accelerated core
_toonverter_core: ModuleType | None
try:
    from toonverter import _toonverter_core

    _RUST_AVAILABLE = True
except ImportError:
    _toonverter_core = None
    _RUST_AVAILABLE = False


def _load_toml_config() -> dict[str, Any]:
    """Load configuration from toonverter.toml in the current directory."""
    config: dict[str, Any] = {}
    cfg_path = Path("toonverter.toml")

    if not cfg_path.exists():
        # Fallback to checking pyproject.toml
        cfg_path = Path("pyproject.toml")
        if not cfg_path.exists():
            return config

    if tomllib is None:
        return config

    try:
        with cfg_path.open("rb") as f:
            data = tomllib.load(f)

            # Check for [tool.toonverter.core] in pyproject.toml
            if cfg_path.name == "pyproject.toml":
                config = data.get("tool", {}).get("toonverter", {}).get("core", {})
            # Check for [core] in toonverter.toml
            else:
                config = data.get("core", {})

    except Exception as e:
        warnings.warn(f"Failed to load configuration from {cfg_path}: {e}", stacklevel=2)

    return config


_file_config = _load_toml_config()


def _get_setting(key: str, env_key: str, default: bool) -> bool:
    """Get boolean value from source (Env > File > Default)."""
    # 1. Environment Variable
    env_val = os.environ.get(env_key)
    if env_val is not None:
        val = env_val.lower()
        if val in ("1", "true", "yes", "on"):
            return True
        if val in ("0", "false", "no", "off"):
            return False

    # 2. Config File
    if key in _file_config:
        return bool(_file_config[key])

    # 3. Default
    return default


# Feature Flags for Rust Integration

# Decoder: Defaults to True as bugs have been resolved
USE_RUST_DECODER = _get_setting("use_rust_decoder", "TOON_USE_RUST_DECODER", True)

# Encoder: Defaults to True as it is stable
USE_RUST_ENCODER = _get_setting("use_rust_encoder", "TOON_USE_RUST_ENCODER", True)

# Validation logic
if USE_RUST_DECODER and not _RUST_AVAILABLE:
    warnings.warn(
        "TOON_USE_RUST_DECODER is set, but the Rust extension is not available. Falling back to Python.",
        stacklevel=2,
    )
    USE_RUST_DECODER = False

if USE_RUST_ENCODER and not _RUST_AVAILABLE:
    warnings.warn(
        "TOON_USE_RUST_ENCODER is set, but the Rust extension is not available. Falling back to Python.",
        stacklevel=2,
    )
    USE_RUST_ENCODER = False

# Expose the core module if needed by other components
# Type as Any to avoid attribute errors since it's a native extension
rust_core: Any = _toonverter_core
