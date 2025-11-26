"""Integration test for Compression Savings and Integrity."""

import json

import pytest

from toonverter import compress, decompress
from toonverter.analysis import count_tokens


class TestCompressionSavings:
    """Verify integrity and measure savings on realistic data."""

    @pytest.fixture
    def sample_log_data(self):
        """Generate a repetitive log-like structure."""
        # Simulates a log file with repeated keys and values
        base_entry = {
            "timestamp": "2023-10-27T10:00:00Z",
            "level": "INFO",
            "service": "payment-processor-v2",
            "region": "us-east-1",
            "environment": "production",
            "message": "Transaction processed successfully",
            "metadata": {"customer_type": "premium", "currency": "USD", "status": "completed"},
        }

        # Create 50 entries, varying only ID
        data = []
        for i in range(50):
            entry = base_entry.copy()
            entry["transaction_id"] = f"txn_{i}"
            data.append(entry)

        return data

    def test_roundtrip_integrity(self, sample_log_data):
        """Verify Data -> Compress -> Decompress -> Data == Original."""
        compressed = compress(sample_log_data)
        restored = decompress(compressed)

        # Convert to JSON strings for strict comparison if direct dict compare is tricky with types
        # But direct comparison is better
        assert restored == sample_log_data

    def test_token_savings(self, sample_log_data):
        """Verify that compression actually saves tokens."""
        # 1. Measure original tokens (as JSON string)
        original_str = json.dumps(sample_log_data)
        original_tokens = count_tokens(original_str)

        # 2. Measure compressed tokens (as JSON string of the wrapper)
        compressed = compress(sample_log_data)
        compressed_str = json.dumps(compressed)
        compressed_tokens = count_tokens(compressed_str)

        # 3. Calculate savings
        savings = original_tokens - compressed_tokens
        percentage = (savings / original_tokens) * 100

        # Expect significant savings (>15% for this repetitive data)
        assert percentage > 15
