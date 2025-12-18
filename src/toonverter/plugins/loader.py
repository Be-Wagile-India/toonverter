"""Plugin loader using entry points."""

import warnings
from importlib.metadata import entry_points  # type: ignore

from toonverter.core.exceptions import PluginError
from toonverter.core.registry import registry


def load_plugins() -> list[str]:
    """Load and register all plugins from entry points.

    Returns:
        List of loaded plugin names

    Raises:
        PluginError: If plugin discovery fails
    """
    loaded = []

    try:
        # Load plugins from entry points
        eps = entry_points(group="toon_converter.plugins")

        for ep in eps:
            try:
                plugin_class = ep.load()
                plugin = plugin_class()

                # Register plugin
                plugin.register(registry)
                plugin.initialize()

                loaded.append(plugin.name)
            except Exception as e:
                # Log error but continue loading other plugins
                warnings.warn(f"Failed to load plugin '{ep.name}': {e}", stacklevel=2)

    except Exception as e:
        msg = f"Failed to discover plugins: {e}"
        raise PluginError(msg) from e

    return loaded
