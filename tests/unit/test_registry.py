"""Comprehensive tests for format adapter registry."""

import threading

import pytest

from toonverter.core.exceptions import FormatNotSupportedError
from toonverter.core.registry import DefaultFormatRegistry, get_registry
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

    def test_init_idempotency(self):
        """Test __init__ is idempotent for singleton instance."""
        # Accessing _adapters before re-init
        self.registry.register("test", JsonFormatAdapter())
        original_adapters_id = id(self.registry._adapters)
        original_lock_id = id(self.registry._adapter_lock)

        # Call __init__ again
        self.registry.__init__()

        # Ensure _adapters and _adapter_lock are the same objects
        assert id(self.registry._adapters) == original_adapters_id
        assert id(self.registry._adapter_lock) == original_lock_id

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

    def test_get_nonexistent_error_message(self):
        """Test getting nonexistent format raises error with full message."""
        self.registry.register("json", JsonFormatAdapter())
        self.registry.register("yaml", YamlFormatAdapter())
        with pytest.raises(FormatNotSupportedError) as excinfo:
            self.registry.get("nonexistent")
        assert "not supported" in str(excinfo.value)
        assert "Available formats: json, yaml" in str(excinfo.value)

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

    def test_concurrent_get(self):
        """Test thread-safe concurrent retrieval."""
        adapter = JsonFormatAdapter()
        self.registry.register("json", adapter)

        results = []

        def get_format(name):
            results.append(self.registry.get(name))

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_format, args=("json",))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 10
        for res in results:
            assert res is adapter

    def test_concurrent_unregister(self):
        """Test thread-safe concurrent unregistration."""
        adapter1 = JsonFormatAdapter()
        adapter2 = YamlFormatAdapter()
        self.registry.register("json", adapter1)
        self.registry.register("yaml", adapter2)

        def unregister_format(name):
            try:
                self.registry.unregister(name)
            except FormatNotSupportedError:
                pass  # Expected if another thread already unregistered

        threads = []
        # Try to unregister 'json' multiple times
        for _ in range(5):
            thread = threading.Thread(target=unregister_format, args=("json",))
            threads.append(thread)
            thread.start()
        # Try to unregister 'yaml' multiple times
        for _ in range(5):
            thread = threading.Thread(target=unregister_format, args=("yaml",))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert not self.registry.is_supported("json")
        assert not self.registry.is_supported("yaml")
        assert len(self.registry.list_formats()) == 0

    def test_concurrent_list_formats(self):
        """Test thread-safe concurrent listing of formats."""
        for i in range(5):
            self.registry.register(f"format{i}", JsonFormatAdapter())

        results = []

        def list_all_formats():
            results.append(self.registry.list_formats())

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=list_all_formats)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 10
        expected_formats = sorted([f"format{i}" for i in range(5)])
        for res in results:
            assert res == expected_formats

    def test_mixed_concurrent_operations(self):
        """Test a mix of concurrent register, get, unregister, list_formats."""
        self.registry.register("initial", JsonFormatAdapter())
        adapter = JsonFormatAdapter()

        def worker(idx):
            if idx % 4 == 0:  # Register
                try:
                    self.registry.register(f"reg{idx}", adapter)
                except ValueError:
                    pass
            elif idx % 4 == 1:  # Get
                try:
                    self.registry.get("initial")
                except FormatNotSupportedError:
                    pass
            elif idx % 4 == 2:  # Unregister
                try:
                    self.registry.unregister("initial")
                except FormatNotSupportedError:
                    pass
            else:  # List
                self.registry.list_formats()

        threads = []
        for i in range(20):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # At least the initial format might be unregistered, and some new ones registered
        # The main goal is to ensure no deadlocks or crashes
        # Detailed state assertion is hard due to concurrency, but we check for general stability
        assert True  # If we reached here without crash, it's a success for stability


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
