import sys
import warnings
from types import ModuleType

# Handle TOML parser import (tomllib for Python 3.11+, tomli backport otherwise)
tomllib: ModuleType | None

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None
        warnings.warn(
            "The 'tomli' library is not installed. TOML configuration will not be loaded.",
            stacklevel=2,
        )
