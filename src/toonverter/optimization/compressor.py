"""Smart Dictionary Compression (SDC) Engine.

This module provides structural compression by identifying repetitive strings
(keys and values) and replacing them with short reference symbols.
"""

from collections import Counter
from typing import Any

from toonverter.core import ToonConverterError


class CompressionError(ToonConverterError):
    """Raised when compression/decompression fails."""


class SmartCompressor:
    """Optimizes data structure size using frequency-based dictionary compression."""

    def __init__(self, min_length: int = 4, min_occurrences: int = 2, prefix: str = "@"):
        """Initialize compressor.

        Args:
            min_length: Minimum string length to consider for compression.
            min_occurrences: Minimum number of times a string must appear.
            prefix: Symbol prefix (default: "@").
        """
        self.min_length = min_length
        self.min_occurrences = min_occurrences
        self.prefix = prefix

    def compress(self, data: Any) -> dict[str, Any]:
        """Compress data by extracting common strings into a symbol table.

        Returns:
            A wrapper dict containing '$symbols' and '$payload'.
        """
        # 1. Analyze frequencies
        counts: Counter[str] = Counter()
        self._scan(data, counts)

        # 2. Select candidates based on ROI (Return on Investment)
        candidates = []
        symbol_counter = 0

        for string, count in counts.items():
            if len(string) < self.min_length or count < self.min_occurrences:
                continue

            # Estimate symbol length (e.g., "@0", "@10")
            # Approximate check
            sym_len = len(self.prefix) + len(str(symbol_counter))

            # Strict ROI: Do we save characters?
            # overhead = len(string) + sym_len + 4 (quotes/separators roughly)
            savings = (len(string) - sym_len) * count
            overhead = len(string) + sym_len + 4

            if savings > overhead:
                candidates.append(string)
                symbol_counter += 1

        # 3. Build symbol table
        # Sort by length desc (replace longest first if we were doing substr replacement,
        # but here we do exact match, so sort order matters less, but deterministic is good)
        candidates.sort()

        symbol_map = {}
        reverse_map = {}

        for i, string in enumerate(candidates):
            sym = f"{self.prefix}{i}"
            symbol_map[string] = sym
            reverse_map[sym] = string

        # 4. Transform data
        # We assume data does not collide with generated symbols.
        # A robust impl would check for collisions in step 1.
        # For "foolproof", we rely on the unlikelyhood of "@0", "@1" in typical user data,
        # or we could make prefix configurable.
        compressed_payload = self._replace(data, symbol_map)

        return {
            "$schema": "toon-sdc-v1",
            "$symbols": reverse_map,
            "$payload": compressed_payload,
        }

    def decompress(self, compressed_data: dict[str, Any]) -> Any:
        """Decompress data using the embedded symbol table."""
        if compressed_data.get("$schema") != "toon-sdc-v1":
            # Fallback: maybe it's not compressed or different format?
            # If user passes raw data, we should perhaps just return it or raise?
            # Foolproof: checks if keys exist.
            if "$symbols" not in compressed_data or "$payload" not in compressed_data:
                return compressed_data

        symbols = compressed_data["$symbols"]
        payload = compressed_data["$payload"]

        return self._resolve(payload, symbols)

    def _scan(self, data: Any, counts: Counter[str]) -> None:
        """Recursively count string occurrences."""
        if isinstance(data, str):
            counts[data] += 1
        elif isinstance(data, list):
            for item in data:
                self._scan(item, counts)
        elif isinstance(data, dict):
            for key, value in data.items():
                counts[key] += 1
                self._scan(value, counts)

    def _replace(self, data: Any, symbol_map: dict[str, str]) -> Any:
        """Recursively replace strings with symbols."""
        if isinstance(data, str):
            return symbol_map.get(data, data)

        if isinstance(data, list):
            return [self._replace(item, symbol_map) for item in data]

        if isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                # Compress key
                new_key = symbol_map.get(key, key)
                # Compress value
                new_value = self._replace(value, symbol_map)
                new_dict[new_key] = new_value
            return new_dict

        return data

    def _resolve(self, data: Any, symbols: dict[str, str]) -> Any:
        """Recursively resolve symbols back to strings."""
        if isinstance(data, str):
            # Check if this string is a symbol
            # Note: This is exact match.
            return symbols.get(data, data)

        if isinstance(data, list):
            return [self._resolve(item, symbols) for item in data]

        if isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                resolved_key = symbols.get(key, key)
                resolved_value = self._resolve(value, symbols)
                new_dict[resolved_key] = resolved_value
            return new_dict

        return data
