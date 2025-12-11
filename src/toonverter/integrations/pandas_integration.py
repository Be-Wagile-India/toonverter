"""Pandas DataFrame integration."""

from collections.abc import Iterator
from typing import Any

from toonverter.core.exceptions import ConversionError
from toonverter.core.types import EncodeOptions
from toonverter.encoders import encode
from toonverter.encoders.stream_encoder import StreamList, ToonStreamEncoder
from toonverter.encoders.toon_encoder import _convert_options


# Optional dependency
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def pandas_to_toon_stream(
    df: "pd.DataFrame", options: EncodeOptions | None = None
) -> Iterator[str]:
    """Convert pandas DataFrame to TOON format stream.

    Memory-efficient conversion for large DataFrames.

    Args:
        df: DataFrame to convert
        options: Encoding options

    Returns:
        Iterator yielding chunks of TOON string

    Raises:
        ImportError: If pandas is not installed
        ConversionError: If conversion fails
    """
    if not PANDAS_AVAILABLE:
        msg = "pandas is required. Install with: pip install toon-converter[integrations]"
        raise ImportError(msg)

    try:
        count = len(df)
        columns = df.columns.tolist()

        def df_iterator():
            # Iterate rows efficiently
            # itertuples is faster than iterrows
            for row in df.itertuples(index=False, name=None):
                yield dict(zip(columns, row, strict=False))

        stream_data = StreamList(iterator=df_iterator(), length=count)

        # Convert options
        toon_options = _convert_options(options or EncodeOptions.tabular())

        encoder = ToonStreamEncoder(toon_options)
        return encoder.iterencode(stream_data)

    except Exception as e:
        msg = f"Failed to stream DataFrame to TOON: {e}"
        raise ConversionError(msg) from e


def pandas_to_toon(
    df: "pd.DataFrame | pd.Series", options: EncodeOptions | None = None, **kwargs: Any
) -> str:
    """Convert pandas DataFrame to TOON format.

    This uses the optimized tabular encoding for maximum efficiency.

    Args:
        df: DataFrame or Series to convert
        options: Encoding options (defaults to tabular preset)
        **kwargs: Additional pandas export options:
            - orient: format for to_dict (default: "records")
            - include_index: whether to include index (default: False)
            - compress: enable compression (ignored, for API compatibility)

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
        msg = "pandas is required. Install with: pip install toon-converter[integrations]"
        raise ImportError(msg)

    try:
        # Handle Series
        if isinstance(df, pd.Series):
            df = df.to_frame()

        # Handle include_index
        if kwargs.get("include_index"):
            df = df.reset_index()

        # Convert DataFrame to list of dicts (optimal for tabular TOON encoding)
        orient = kwargs.get("orient", "records")
        data = df.to_dict(orient=orient)

        options = options or EncodeOptions.tabular()
        return encode(data, options)
    except Exception as e:
        msg = f"Failed to convert DataFrame to TOON: {e}"
        raise ConversionError(msg) from e


def toon_to_pandas(toon_str: str, as_series: bool = False) -> Any:
    """Convert TOON format to pandas DataFrame.

    Args:
        toon_str: TOON format string (tabular format)
        as_series: Return as Series if possible (default: False)

    Returns:
        pandas DataFrame or Series (or scalar if single value and as_series is True)

    Raises:
        ImportError: If pandas is not installed
        ConversionError: If conversion fails

    Examples:
        >>> toon_str = "name,age\\nAlice,30\\nBob,25"
        >>> df = toon_to_pandas(toon_str)
    """
    if not PANDAS_AVAILABLE:
        msg = "pandas is required. Install with: pip install toon-converter[integrations]"
        raise ImportError(msg)

    try:
        from toonverter.decoders import decode

        data = decode(toon_str)

        # Handle empty list or valid list of dicts
        if isinstance(data, list):
            if not data:
                df = pd.DataFrame()
            elif isinstance(data[0], dict):
                df = pd.DataFrame(data)
            else:
                # List of primitives?
                df = pd.DataFrame(data)

            if as_series:
                return df.squeeze()
            return df

        msg = "TOON data must be in tabular format (list of dicts)"
        raise ConversionError(msg)
    except Exception as e:
        msg = f"Failed to convert TOON to DataFrame: {e}"
        raise ConversionError(msg) from e
