"""Performance benchmarks for optimization features."""

import pytest


try:
    from toonverter.analysis.deduplication import SemanticDeduplicator

    HAS_DEDUPLICATION = True
except ImportError:
    HAS_DEDUPLICATION = False

from toonverter.optimization.compressor import SmartCompressor
from toonverter.optimization.engine import ContextOptimizer


class TestCompressionPerformance:
    """Benchmark Smart Dictionary Compression."""

    def setup_method(self):
        self.compressor = SmartCompressor(min_length=3, min_occurrences=2)
        # Create a repetitive dataset
        self.large_data = {
            "records": [
                {
                    "status": "active",
                    "role": "administrator",
                    "department": "engineering",
                    "location": "san_francisco_office",
                    "metadata": {"source": "internal_system", "version": "v1.2.3"},
                }
                for _ in range(1000)
            ]
        }
        self.compressed_data = self.compressor.compress(self.large_data)

    def test_compress_large_dataset(self, benchmark):
        """Benchmark compression of repetitive data."""
        result = benchmark(self.compressor.compress, self.large_data)
        assert "$symbols" in result

    def test_decompress_large_dataset(self, benchmark):
        """Benchmark decompression."""
        result = benchmark(self.compressor.decompress, self.compressed_data)
        assert len(result["records"]) == 1000


class TestContextOptimizerPerformance:
    """Benchmark Context Optimization (Pruning/Truncation)."""

    def setup_method(self):
        self.optimizer = ContextOptimizer(budget=5000)
        # Create deep/large structure
        self.data = {
            "users": [
                {
                    "id": i,
                    "bio": "This is a very long biography string that might need truncation if we are over budget "
                    * 10,
                    "details": {
                        "history": ["log_entry_" + str(j) for j in range(50)],
                        "scores": [float(x) / 3.0 for x in range(20)],
                    },
                }
                for i in range(100)
            ]
        }

    def test_optimize_pass(self, benchmark):
        """Benchmark optimization pass."""
        # Note: We clone data inside optimize, so this measures copy + optimize time
        result = benchmark(self.optimizer.optimize, self.data)
        assert result is not None


@pytest.mark.skipif(not HAS_DEDUPLICATION, reason="Semantic dependencies not installed")
class TestDeduplicationPerformance:
    """Benchmark Semantic Deduplication."""

    def setup_method(self):
        # Pre-instantiate to measure processing time, not model load time per benchmark iteration
        self.deduplicator = SemanticDeduplicator(threshold=0.9)
        # Create a list with semantic duplicates
        self.data = {
            "phrases": [
                "Hello world",
                "Hi there world",  # distinct
                "Hello world",  # exact dupe
                "Hello world!",  # near dupe
                "Greetings earthlings",
            ]
            * 50
        }

    def test_deduplicate_list(self, benchmark):
        """Benchmark deduplication of text list."""
        if not HAS_DEDUPLICATION:
            return

        def run_dedup():
            return self.deduplicator.optimize(self.data)

        result = benchmark(run_dedup)
        assert len(result["phrases"]) < len(self.data["phrases"])
