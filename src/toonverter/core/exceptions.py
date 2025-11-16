"""Custom exception hierarchy for TOON Converter."""


class ToonConverterError(Exception):
    """Base exception for all TOON Converter errors."""

    pass


class ConversionError(ToonConverterError):
    """Raised when data conversion fails."""

    pass


class EncodingError(ToonConverterError):
    """Raised when encoding to TOON format fails."""

    pass


class DecodingError(ToonConverterError):
    """Raised when decoding from TOON format fails."""

    pass


class ValidationError(ToonConverterError):
    """Raised when input validation fails."""

    pass


class FormatNotSupportedError(ToonConverterError):
    """Raised when a format is not supported."""

    pass


class PluginError(ToonConverterError):
    """Raised when plugin loading or registration fails."""

    pass


class TokenCountError(ToonConverterError):
    """Raised when token counting fails."""

    pass


class FileOperationError(ToonConverterError):
    """Raised when file read/write operations fail."""

    pass
