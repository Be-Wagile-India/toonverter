"""Format adapter registry implementing the Factory pattern.

This module provides a thread-safe singleton registry for format adapters.
"""

import threading
from typing import Optional

from .exceptions import FormatNotSupportedError
from .interfaces import FormatAdapter, FormatRegistry


class DefaultFormatRegistry(FormatRegistry):
    """Default implementation of format adapter registry.

    This class implements the Singleton pattern to ensure a single
    global registry instance. Thread-safe for concurrent access.
    """

    _instance: Optional["DefaultFormatRegistry"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "DefaultFormatRegistry":
        """Create or return the singleton instance.

        Returns:
            Singleton registry instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._adapters: dict[str, FormatAdapter] = {}
                    cls._instance._adapter_lock = threading.RLock()
        return cls._instance

    def register(self, format_name: str, adapter: FormatAdapter) -> None:
        """Register a format adapter.

        Args:
            format_name: Format identifier (lowercase)
            adapter: FormatAdapter instance

        Raises:
            ValueError: If format already registered or invalid
        """
        if not format_name:
            raise ValueError("Format name cannot be empty")

        if not isinstance(adapter, FormatAdapter):
            raise TypeError(f"Adapter must be a FormatAdapter instance, got {type(adapter)}")

        format_name = format_name.lower()

        with self._adapter_lock:
            if format_name in self._adapters:
                raise ValueError(f"Format '{format_name}' is already registered")
            self._adapters[format_name] = adapter

    def get(self, format_name: str) -> FormatAdapter:
        """Retrieve format adapter by name.

        Args:
            format_name: Format identifier (case-insensitive)

        Returns:
            FormatAdapter instance

        Raises:
            FormatNotSupportedError: If format not found
        """
        if not format_name:
            raise FormatNotSupportedError("Format name cannot be empty")

        format_name = format_name.lower()

        with self._adapter_lock:
            if format_name not in self._adapters:
                raise FormatNotSupportedError(
                    f"Format '{format_name}' is not supported. "
                    f"Available formats: {', '.join(sorted(self._adapters.keys()))}"
                )
            return self._adapters[format_name]

    def unregister(self, format_name: str) -> None:
        """Unregister a format adapter.

        Args:
            format_name: Format identifier (case-insensitive)

        Raises:
            FormatNotSupportedError: If format not found
        """
        format_name = format_name.lower()

        with self._adapter_lock:
            if format_name not in self._adapters:
                raise FormatNotSupportedError(f"Format '{format_name}' is not registered")
            del self._adapters[format_name]

    def list_formats(self) -> list[str]:
        """List all registered format names.

        Returns:
            Sorted list of format identifiers
        """
        with self._adapter_lock:
            return sorted(self._adapters.keys())

    def is_supported(self, format_name: str) -> bool:
        """Check if format is supported.

        Args:
            format_name: Format identifier (case-insensitive)

        Returns:
            True if format is registered
        """
        if not format_name:
            return False

        format_name = format_name.lower()

        with self._adapter_lock:
            return format_name in self._adapters

    def clear(self) -> None:
        """Clear all registered adapters.

        Warning: This is primarily for testing. Use with caution.
        """
        with self._adapter_lock:
            self._adapters.clear()


# Global singleton instance
registry = DefaultFormatRegistry()


def get_registry() -> FormatRegistry:
    """Get the global format registry instance.

    Returns:
        Global FormatRegistry singleton
    """
    return registry
