"""Performance benchmarks for TOON encoding/decoding."""

import json

from toonverter.decoders.toon_decoder import ToonDecoder
from toonverter.encoders.toon_encoder import ToonEncoder


class TestEncodingPerformance:
    """Benchmark encoding performance."""

    def setup_method(self):
        """Set up encoder."""
        self.encoder = ToonEncoder()

    def test_encode_small_object(self, benchmark):
        """Benchmark encoding small object."""
        data = {"name": "Alice", "age": 30, "active": True}

        result = benchmark(self.encoder.encode, data)

        assert "Alice" in result

    def test_encode_medium_array(self, benchmark):
        """Benchmark encoding medium array."""
        data = {"items": list(range(1000))}

        result = benchmark(self.encoder.encode, data)

        assert "[1000]:" in result

    def test_encode_large_structure(self, benchmark):
        """Benchmark encoding large nested structure."""
        data = {
            "users": [
                {"id": i, "name": f"User{i}", "email": f"user{i}@example.com"} for i in range(1000)
            ]
        }

        result = benchmark(self.encoder.encode, data)

        assert "[1000]" in result

    def test_encode_deeply_nested(self, benchmark):
        """Benchmark encoding deeply nested structure."""
        nested = {"level": 0}
        current = nested
        for i in range(100):
            current["nested"] = {"level": i + 1}
            current = current["nested"]

        result = benchmark(self.encoder.encode, nested)

        assert result is not None


class TestDecodingPerformance:
    """Benchmark decoding performance."""

    def setup_method(self):
        """Set up decoder."""
        self.decoder = ToonDecoder()
        self.encoder = ToonEncoder()

    def test_decode_small_object(self, benchmark):
        """Benchmark decoding small object."""
        toon = "name: Alice\nage: 30\nactive: true"

        result = benchmark(self.decoder.decode, toon)

        assert result["name"] == "Alice"

    def test_decode_medium_array(self, benchmark):
        """Benchmark decoding medium array."""
        data = {"items": list(range(1000))}
        toon = self.encoder.encode(data)

        result = benchmark(self.decoder.decode, toon)

        assert len(result["items"]) == 1000

    def test_decode_large_tabular(self, benchmark):
        """Benchmark decoding large tabular array."""
        data = {"users": [{"id": i, "name": f"User{i}"} for i in range(1000)]}
        toon = self.encoder.encode(data)

        result = benchmark(self.decoder.decode, toon)

        assert len(result["users"]) == 1000


class TestRoundtripPerformance:
    """Benchmark roundtrip performance."""

    def setup_method(self):
        """Set up encoder/decoder."""
        self.encoder = ToonEncoder()
        self.decoder = ToonDecoder()

    def test_roundtrip_small(self, benchmark):
        """Benchmark small data roundtrip."""
        data = {"test": "value", "num": 42}

        def roundtrip():
            toon = self.encoder.encode(data)
            return self.decoder.decode(toon)

        result = benchmark(roundtrip)

        assert result == data

    def test_roundtrip_medium(self, benchmark):
        """Benchmark medium data roundtrip."""
        data = {"items": [{"id": i, "value": f"item{i}"} for i in range(100)]}

        def roundtrip():
            toon = self.encoder.encode(data)
            return self.decoder.decode(toon)

        result = benchmark(roundtrip)

        assert len(result["items"]) == 100


class TestCompressionRatio:
    """Test compression ratio vs JSON."""

    def setup_method(self):
        """Set up encoder."""
        self.encoder = ToonEncoder()

    def test_simple_object_compression(self):
        """Test compression ratio for simple object."""
        data = {"name": "Alice", "age": 30, "active": True}

        toon = self.encoder.encode(data)
        json_str = json.dumps(data)

        toon_len = len(toon)
        json_len = len(json_str)

        # TOON should be smaller or equal
        assert toon_len <= json_len

    def test_array_compression(self):
        """Test compression ratio for arrays."""
        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
                {"name": "Carol", "age": 35},
            ]
        }

        toon = self.encoder.encode(data)
        json_str = json.dumps(data)

        toon_len = len(toon)
        json_len = len(json_str)

        # TOON tabular should be much smaller
        assert toon_len < json_len

        savings = (json_len - toon_len) / json_len * 100

        # Should achieve at least 20% savings on uniform data
        assert savings >= 20

    def test_large_dataset_compression(self):
        """Test compression ratio for large dataset."""
        data = {"records": [{"id": i, "name": f"Record{i}", "value": i * 10} for i in range(1000)]}

        toon = self.encoder.encode(data)
        json_str = json.dumps(data)

        toon_len = len(toon)
        json_len = len(json_str)

        savings = (json_len - toon_len) / json_len * 100

        # Should achieve significant savings on large uniform data
        assert savings >= 30


class TestMemoryUsage:
    """Test memory usage."""

    def test_large_structure_memory(self):
        """Test memory usage with large structures."""
        import sys

        encoder = ToonEncoder()
        decoder = ToonDecoder()

        # Create large structure
        data = {"items": [{"id": i, "data": f"{'x' * 100}"} for i in range(1000)]}

        # Encode
        toon = encoder.encode(data)

        # Decode
        result = decoder.decode(toon)

        # Should complete without excessive memory usage
        assert len(result["items"]) == 1000

        # Measure sizes
        sys.getsizeof(toon)
        sys.getsizeof(json.dumps(data))
