"""Configuration settings for Toonverter."""

import os
import sys
import warnings
from pathlib import Path
from types import ModuleType
from typing import Any


# Conditional import for tomllib/tomli
_tomllib: ModuleType | None = None

if sys.version_info >= (3, 11):
    try:
        import tomllib as _actual_tomllib

        _tomllib = _actual_tomllib
    except ImportError:
        warnings.warn(
            "The 'tomllib' library (built-in for Python 3.11+) could not be imported.",
            stacklevel=2,
        )
else:
    try:
        import tomli as _actual_tomllib

        _tomllib = _actual_tomllib
    except ImportError:
        warnings.warn(
            "The 'tomli' library is not installed. TOML configuration will not be loaded.",
            stacklevel=2,
        )


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

    if _tomllib is None:
        return config

    try:
        with cfg_path.open("rb") as f:
            data = _tomllib.load(f)

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


def _get_int_setting(key: str, env_key: str, default: int) -> int:
    """Get integer value from source (Env > File > Default)."""
    # 1. Environment Variable
    env_val = os.environ.get(env_key)
    if env_val is not None:
        try:
            return int(env_val)
        except ValueError:
            warnings.warn(
                f"Invalid integer value for environment variable {env_key}. Using default.",
                stacklevel=2,
            )

    # 2. Config File
    if key in _file_config:
        file_val = _file_config[key]
        if isinstance(file_val, int):
            return file_val
        warnings.warn(
            f"Invalid integer value for '{key}' in config file. Using default.",
            stacklevel=2,
        )

    # 3. Default
    return default


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

# Strict Rust Build: Defaults to False. If True, will raise an ImportError if Rust is enabled but not available.
STRICT_RUST_BUILD = _get_setting("strict_rust_build", "TOON_STRICT_RUST_BUILD", False)

# Parallelism Threshold: Default to 1000 items
PARALLELISM_THRESHOLD = _get_int_setting(
    "parallelism_threshold", "TOON_PARALLELISM_THRESHOLD", 1000
)

# Validation logic
if not _RUST_AVAILABLE:
    msg = "Rust extension is not available."
    if STRICT_RUST_BUILD:
        if USE_RUST_DECODER:
            error_msg = f"{msg} TOON_USE_RUST_DECODER is set, but the Rust extension is not available and TOON_STRICT_RUST_BUILD is True."
            raise ImportError(error_msg)
        if USE_RUST_ENCODER:
            error_msg = f"{msg} TOON_USE_RUST_ENCODER is set, but the Rust extension is not available and TOON_STRICT_RUST_BUILD is True."
            raise ImportError(error_msg)
    else:
        if USE_RUST_DECODER:
            warnings.warn(
                "TOON_USE_RUST_DECODER is set, but the Rust extension is not available. Falling back to Python.",
                stacklevel=2,
            )
            USE_RUST_DECODER = False

        if USE_RUST_ENCODER:
            warnings.warn(
                "TOON_USE_RUST_ENCODER is set, but the Rust extension is not available. Falling back to Python.",
                stacklevel=2,
            )
            USE_RUST_ENCODER = False

# Expose the core module if needed by other components
# Type as Any to avoid attribute errors since it's a native extension
rust_core: Any = _toonverter_core
