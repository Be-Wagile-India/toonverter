"""Comprehensive tests for format adapter registry."""

import pytest
import threading
from toonverter.core.registry import DefaultFormatRegistry, get_registry
from toonverter.core.exceptions import FormatNotSupportedError
from toonverter.formats.json_format import JsonFormatAdapter
from toonverter.formats.yaml_format import YamlFormatAdapter


class TestDefaultFormatRegistry:
    """Test DefaultFormatRegistry functionality."""

    def setup_method(self):
        """Set up fresh registry for each test."""
        self.registry = DefaultFormatRegistry()
        self.registry.clear()

    def teardown_method(self):
        """Clean up registry after each test."""
        self.registry.clear()

    def test_singleton_pattern(self):
        """Test singleton pattern returns same instance."""
        registry1 = DefaultFormatRegistry()
        registry2 = DefaultFormatRegistry()
        assert registry1 is registry2

    def test_register_adapter(self):
        """Test registering a format adapter."""
        adapter = JsonFormatAdapter()
        self.registry.register("json", adapter)
        assert self.registry.is_supported("json")

    def test_register_case_insensitive(self):
        """Test format registration is case-insensitive."""
        adapter = JsonFormatAdapter()
        self.registry.register("JSON", adapter)
        assert self.registry.is_supported("json")
        assert self.registry.is_supported("JSON")

    def test_register_duplicate_raises_error(self):
        """Test registering duplicate format raises error."""
        adapter = JsonFormatAdapter()
        self.registry.register("json", adapter)
        with pytest.raises(ValueError, match="already registered"):
            self.registry.register("json", adapter)

    def test_register_empty_name_raises_error(self):
        """Test registering with empty name raises error."""
        adapter = JsonFormatAdapter()
        with pytest.raises(ValueError, match="cannot be empty"):
            self.registry.register("", adapter)

    def test_register_non_adapter_raises_error(self):
        """Test registering non-adapter object raises error."""
        with pytest.raises(TypeError, match="must be a FormatAdapter"):
            self.registry.register("test", "not an adapter")

    def test_get_adapter(self):
        """Test retrieving registered adapter."""
        adapter = JsonFormatAdapter()
        self.registry.register("json", adapter)
        retrieved = self.registry.get("json")
        assert retrieved is adapter

    def test_get_case_insensitive(self):
        """Test getting adapter is case-insensitive."""
        adapter = JsonFormatAdapter()
        self.registry.register("json", adapter)
        assert self.registry.get("JSON") is adapter
        assert self.registry.get("Json") is adapter

    def test_get_nonexistent_raises_error(self):
        """Test getting nonexistent format raises error."""
        with pytest.raises(FormatNotSupportedError, match="not supported"):
            self.registry.get("nonexistent")

    def test_get_empty_name_raises_error(self):
        """Test getting with empty name raises error."""
        with pytest.raises(FormatNotSupportedError, match="cannot be empty"):
            self.registry.get("")

    def test_unregister_adapter(self):
        """Test unregistering an adapter."""
        adapter = JsonFormatAdapter()
        self.registry.register("json", adapter)
        assert self.registry.is_supported("json")
        self.registry.unregister("json")
        assert not self.registry.is_supported("json")

    def test_unregister_nonexistent_raises_error(self):
        """Test unregistering nonexistent format raises error."""
        with pytest.raises(FormatNotSupportedError, match="not registered"):
            self.registry.unregister("nonexistent")

    def test_list_formats_empty(self):
        """Test listing formats when registry is empty."""
        assert self.registry.list_formats() == []

    def test_list_formats_sorted(self):
        """Test listing formats returns sorted list."""
        self.registry.register("yaml", YamlFormatAdapter())
        self.registry.register("json", JsonFormatAdapter())
        formats = self.registry.list_formats()
        assert formats == ["json", "yaml"]

    def test_is_supported_true(self):
        """Test is_supported returns True for registered format."""
        adapter = JsonFormatAdapter()
        self.registry.register("json", adapter)
        assert self.registry.is_supported("json")

    def test_is_supported_false(self):
        """Test is_supported returns False for unregistered format."""
        assert not self.registry.is_supported("nonexistent")

    def test_is_supported_empty_name(self):
        """Test is_supported returns False for empty name."""
        assert not self.registry.is_supported("")

    def test_clear_registry(self):
        """Test clearing all adapters."""
        self.registry.register("json", JsonFormatAdapter())
        self.registry.register("yaml", YamlFormatAdapter())
        assert len(self.registry.list_formats()) == 2
        self.registry.clear()
        assert len(self.registry.list_formats()) == 0

    def test_concurrent_registration(self):
        """Test thread-safe concurrent registration."""
        def register_format(name):
            try:
                adapter = JsonFormatAdapter()
                self.registry.register(name, adapter)
            except ValueError:
                pass  # Duplicate registration is expected in concurrent scenario

        threads = []
        for i in range(10):
            thread = threading.Thread(target=register_format, args=(f"format{i}",))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All formats should be registered
        formats = self.registry.list_formats()
        assert len(formats) == 10


class TestGetRegistry:
    """Test global registry access function."""

    def test_get_registry_returns_singleton(self):
        """Test get_registry returns the singleton instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_get_registry_is_default_registry(self):
        """Test get_registry returns DefaultFormatRegistry instance."""
        registry = get_registry()
        assert isinstance(registry, DefaultFormatRegistry)
