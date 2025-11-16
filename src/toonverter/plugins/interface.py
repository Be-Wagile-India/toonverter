"""Plugin interface implementation."""

from toonverter.core.interfaces import Plugin as BasePlugin


# Re-export for convenience
Plugin = BasePlugin

__all__ = ["Plugin"]
