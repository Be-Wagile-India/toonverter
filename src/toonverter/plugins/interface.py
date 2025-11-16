"""Plugin interface implementation."""

from ..core.interfaces import Plugin as BasePlugin

# Re-export for convenience
Plugin = BasePlugin

__all__ = ["Plugin"]
