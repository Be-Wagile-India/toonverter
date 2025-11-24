"""TOON format adapter."""

from collections.abc import Iterator
from typing import Any

from toonverter.core.spec import ToonDecodeOptions
from toonverter.core.types import DecodeOptions, EncodeOptions
from toonverter.decoders import decode as toon_decode
from toonverter.decoders.stream_decoder import StreamDecoder
from toonverter.encoders import encode as toon_encode
from toonverter.encoders.stream_encoder import ToonStreamEncoder
from toonverter.encoders.toon_encoder import _convert_options as _convert_encode_options

from .base import BaseFormatAdapter


def _convert_decode_options(
    options: DecodeOptions | ToonDecodeOptions | None,
) -> ToonDecodeOptions | None:
    if options is None:
        return None
    if isinstance(options, ToonDecodeOptions):
        return options
    if isinstance(options, DecodeOptions):
        return ToonDecodeOptions(
            strict=options.strict,
            type_inference=options.type_inference,
        )
    return None


class ToonFormatAdapter(BaseFormatAdapter):
    """Adapter for TOON (Token-Optimized Object Notation) format."""

    def __init__(self) -> None:
        """Initialize TOON format adapter."""
        super().__init__("toon")

    def encode(self, data: Any, options: EncodeOptions | None = None) -> str:
        """Encode data to TOON format.

        Args:
            data: Data to encode
            options: Encoding options

        Returns:
            TOON formatted string
        """
        return toon_encode(data, options)

    def decode(self, data_str: str, options: DecodeOptions | None = None) -> Any:
        """Decode TOON format to Python data.

        Args:
            data_str: TOON format string
            options: Decoding options

        Returns:
            Decoded Python data
        """
        toon_options = _convert_decode_options(options)
        return toon_decode(data_str, toon_options)

    def validate(self, data_str: str) -> bool:
        """Validate TOON format string.

        Args:
            data_str: String to validate

        Returns:
            True if valid TOON format
        """
        try:
            toon_decode(data_str)
            return True
        except Exception:
            return False

    def supports_streaming(self) -> bool:
        """
        Check if the adapter supports streaming operations.

        Returns:
            True (TOON supports streaming encoding)
        """
        return True

    def encode_stream(self, data: Any, **kwargs: Any) -> Iterator[str]:
        """
        Encode data to the format as a stream of strings.

        Args:
            data: The data to encode
            **kwargs: Additional encoding options (mapped to ToonEncodeOptions)

        Returns:
            Iterator[str]: An iterator yielding chunks of the encoded data
        """
        # Convert options consistent with standard encoder
        options_obj = kwargs.get("options")
        toon_options = _convert_encode_options(options_obj)

        encoder = ToonStreamEncoder(toon_options)
        return encoder.iterencode(data)

    def decode_stream(self, stream: Iterator[str], **kwargs: Any) -> Iterator[Any]:
        """
        Decode data from a stream of strings.

        Args:
            stream: An iterator yielding chunks of the encoded data (lines)
            **kwargs: Additional decoding options

        Returns:
            Iterator[Any]: An iterator yielding decoded objects
        """
        options_obj = kwargs.get("options")
        toon_options = _convert_decode_options(options_obj)

        decoder = StreamDecoder(toon_options)
        return decoder.decode_stream(stream)
