"""Plugin loader using entry points."""

import sys
from typing import Any

from ..core.exceptions import PluginError
from ..core.registry import registry

if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points  # type: ignore


def load_plugins() -> list[str]:
    """Load and register all plugins from entry points.

    Returns:
        List of loaded plugin names

    Raises:
        PluginError: If plugin loading fails
    """
    loaded = []

    try:
        # Load plugins from entry points
        if sys.version_info >= (3, 10):
            eps = entry_points(group="toon_converter.plugins")
        else:
            eps = entry_points().get("toon_converter.plugins", [])

        for ep in eps:
            try:
                plugin_class = ep.load()
                plugin = plugin_class()

                # Register plugin
                plugin.register(registry)
                plugin.initialize()

                loaded.append(plugin.name)
            except Exception as e:
                raise PluginError(f"Failed to load plugin '{ep.name}': {e}") from e

    except Exception as e:
        if isinstance(e, PluginError):
            raise
        raise PluginError(f"Failed to discover plugins: {e}") from e

    return loaded
