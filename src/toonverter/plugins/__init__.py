"""Plugin system for extensibility."""

from .interface import Plugin
from .loader import load_plugins


__all__ = ["Plugin", "load_plugins"]
