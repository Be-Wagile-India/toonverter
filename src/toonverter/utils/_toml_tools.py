import sys
import warnings
from types import ModuleType


# Handle TOML parser import (tomllib for Python 3.11+, tomli backport otherwise)
_tomllib_module: ModuleType | None

if sys.version_info >= (3, 11):
    import tomllib as _tomllib_module
else:
    try:
        import tomli as _tomllib_module
    except ImportError:
        _tomllib_module = None
        warnings.warn(
            "The 'tomli' library is not installed. TOML configuration will not be loaded.",
            stacklevel=2,
        )

tomllib = _tomllib_module
