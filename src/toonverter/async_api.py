from typing import Any

from .core import ConversionResult, DecodeOptions, EncodeOptions, registry
from .utils.async_io import _run_in_thread, async_read_file, async_write_file


async def async_convert(
    source: str,
    target: str,
    from_format: str,
    to_format: str,
    **options: Any,
) -> ConversionResult:
    """Convert data from one format to another asynchronously.

    Args:
        source: Path to source file
        target: Path to target file
        from_format: Source format (e.g., 'json', 'yaml')
        to_format: Target format (e.g., 'toon')
        **options: Additional conversion options

    Returns:
        ConversionResult with conversion details
    """
    try:
        # 1. Read source file asynchronously
        source_data_str = await async_read_file(source)

        # Use the options when decoding/encoding
        decode_opts = DecodeOptions(**options) if options else None
        encode_opts = EncodeOptions(**options) if options else None

        # 2. Decode from source format (synchronous core logic)
        source_adapter = registry.get(from_format)
        data = source_adapter.decode(source_data_str, decode_opts)

        # 3. Encode to target format (synchronous core logic)
        target_adapter = registry.get(to_format)
        target_data_str = target_adapter.encode(data, encode_opts)

        # 4. Write target file asynchronously
        await async_write_file(target, target_data_str)

        # (Token counting logic is intentionally omitted here for brevity,
        # but in a complete implementation, it would be run via to_thread)

        return ConversionResult(
            success=True,
            source_format=from_format,
            target_format=to_format,
            data=data,
            source_tokens=0,  # Placeholder
            target_tokens=0,  # Placeholder
        )
    except Exception as e:
        return ConversionResult(
            success=False, source_format=from_format, target_format=to_format, error=str(e)
        )


async def async_encode(data: Any, to_format: str = "toon", **options: Any) -> str:
    """Encode data to specified format asynchronously."""
    adapter = registry.get(to_format)
    encode_opts = EncodeOptions(**options) if options else None

    # Run the potentially blocking encoding logic in a thread
    return await _run_in_thread(adapter.encode, data, encode_opts)


async def async_decode(data_str: str, from_format: str = "toon", **options: Any) -> Any:
    """Decode data from specified format asynchronously."""
    adapter = registry.get(from_format)
    decode_opts = DecodeOptions(**options) if options else None

    # Run the potentially blocking decoding logic in a thread
    return await _run_in_thread(adapter.decode, data_str, decode_opts)
