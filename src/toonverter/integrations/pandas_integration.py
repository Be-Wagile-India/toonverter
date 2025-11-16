"""Pandas DataFrame integration."""

from typing import Any, Optional

from ..core.exceptions import ConversionError
from ..core.types import EncodeOptions
from ..encoders import encode

# Optional dependency
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def pandas_to_toon(df: "pd.DataFrame", options: Optional[EncodeOptions] = None) -> str:
    """Convert pandas DataFrame to TOON format.

    This uses the optimized tabular encoding for maximum efficiency.

    Args:
        df: DataFrame to convert
        options: Encoding options (defaults to tabular preset)

    Returns:
        TOON format string

    Raises:
        ImportError: If pandas is not installed
        ConversionError: If conversion fails

    Examples:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [30, 25]})
        >>> toon_str = pandas_to_toon(df)
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required. Install with: pip install toon-converter[integrations]")

    try:
        # Convert DataFrame to list of dicts (optimal for tabular TOON encoding)
        data = df.to_dict("records")
        options = options or EncodeOptions.tabular()
        return encode(data, options)
    except Exception as e:
        raise ConversionError(f"Failed to convert DataFrame to TOON: {e}") from e


def toon_to_pandas(toon_str: str) -> "pd.DataFrame":
    """Convert TOON format to pandas DataFrame.

    Args:
        toon_str: TOON format string (tabular format)

    Returns:
        pandas DataFrame

    Raises:
        ImportError: If pandas is not installed
        ConversionError: If conversion fails

    Examples:
        >>> toon_str = "name,age\\nAlice,30\\nBob,25"
        >>> df = toon_to_pandas(toon_str)
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required. Install with: pip install toon-converter[integrations]")

    try:
        from ..decoders import decode

        data = decode(toon_str)

        if isinstance(data, list) and data and isinstance(data[0], dict):
            return pd.DataFrame(data)
        else:
            raise ConversionError("TOON data must be in tabular format (list of dicts)")
    except Exception as e:
        raise ConversionError(f"Failed to convert TOON to DataFrame: {e}") from e
