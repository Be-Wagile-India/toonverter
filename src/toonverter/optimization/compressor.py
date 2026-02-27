from collections import Counter
from typing import Any

from toonverter.core import ToonConverterError


class CompressionError(ToonConverterError):
    pass


class SmartCompressor:
    def __init__(self, min_length: int = 4, min_occurrences: int = 2, prefix: str = "@") -> None:
        self.min_length = min_length
        self.min_occurrences = min_occurrences
        self.prefix = prefix

    def compress(self, data: Any) -> dict[str, Any]:
        counts: Counter[str] = Counter()
        self._scan(data, counts)

        candidates = []
        symbol_counter = 0

        for string, count in counts.items():
            if len(string) < self.min_length or count < self.min_occurrences:
                continue
            sym_len = len(self.prefix) + len(str(symbol_counter))
            savings = (len(string) - sym_len) * count
            overhead = len(string) + sym_len + 4
            if savings > overhead:
                candidates.append(string)
                symbol_counter += 1

        candidates.sort()
        symbol_map = {}
        reverse_map = {}

        # Collect all strings in data to avoid collisions
        all_strings = set(counts.keys())

        symbol_idx = 0
        for string in candidates:
            # Find next available symbol that doesn't exist in original data
            while True:
                sym = f"{self.prefix}{symbol_idx}"
                if sym not in all_strings:
                    break
                symbol_idx += 1

            symbol_map[string] = sym
            reverse_map[sym] = string
            symbol_idx += 1

        compressed_payload = self._replace(data, symbol_map)

        return {"$schema": "toon-sdc-v1", "$symbols": reverse_map, "$payload": compressed_payload}

    def decompress(self, compressed_data: dict[str, Any]) -> Any:
        if compressed_data.get("$schema") != "toon-sdc-v1":
            if "$symbols" not in compressed_data or "$payload" not in compressed_data:
                return compressed_data

        symbols = compressed_data["$symbols"]
        payload = compressed_data["$payload"]
        return self._resolve(payload, symbols)

    def _scan(self, data: Any, counts: Counter[str]) -> None:
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
        if isinstance(data, str):
            return symbol_map.get(data, data)

        if isinstance(data, list):
            return [self._replace(item, symbol_map) for item in data]

        if isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                new_key = symbol_map.get(key, key)
                new_value = self._replace(value, symbol_map)
                new_dict[new_key] = new_value
            return new_dict

        return data

    def _resolve(self, data: Any, symbols: dict[str, str]) -> Any:
        if isinstance(data, str):
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
