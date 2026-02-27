"""Custom exception hierarchy for TOON Converter."""


class ToonConverterError(Exception):
    """Base exception for all TOON Converter errors."""


class ConversionError(ToonConverterError):
    """Raised when data conversion fails."""


class EncodingError(ToonConverterError):
    """Raised when encoding to TOON format fails."""


class DecodingError(ToonConverterError):
    """Raised when decoding from TOON format fails."""


class ToonDecodeError(DecodingError):
    """Raised for specific errors during TOON decoding process."""


class ValidationError(ToonConverterError):
    """Raised when input validation fails."""


class FormatNotSupportedError(ToonConverterError):
    """Raised when a format is not supported."""


class PluginError(ToonConverterError):
    """Raised when plugin loading or registration fails."""


class TokenCountError(ToonConverterError):
    """Raised when token counting fails."""


class FileOperationError(ToonConverterError):
    """Raised when file read/write operations fail."""


class ProcessingError(ToonConverterError):
    """Raised when a general processing error occurs."""


class InternalError(ToonConverterError):
    """Raised when an internal error occurs (e.g., in the Rust core)."""
