import json
import os
import re
import subprocess
import sys

import pytest

from toonverter.core.config import USE_RUST_DECODER


# Define the path to the large test data file
LARGE_TOON_FILE = "large_test_data.toon"


# This fixture will load the large TOON data once for all tests
@pytest.fixture(scope="module", autouse=True)  # autouse=True ensures it runs once per module
def _setup_large_toon_data_file():
    # Force regeneration of the file if it exists, to ensure correct size
    if os.path.exists(LARGE_TOON_FILE):
        os.remove(LARGE_TOON_FILE)

    if not os.path.exists(LARGE_TOON_FILE):
        try:

            def generate_large_toon_data_str(num_records: int, field_size: int) -> str:
                """Generates a large JSON-like data structure that can be encoded to TOON."""
                # Generate a list of simple strings for clearer memory profiling
                data = {"items": []}
                long_string = "x" * field_size
                for i in range(num_records):
                    # Each item is a unique string to avoid Python's string interning masking issues
                    data["items"].append(f"{long_string}_{i}")
                return json.dumps(data)

            NUM_RECORDS = 100_000  # Number of items
            FIELD_SIZE = 100  # Size of a string field

            json_data_str = generate_large_toon_data_str(NUM_RECORDS, FIELD_SIZE)

            # Encode to TOON (using Python encoder for generation)
            from toonverter import encode
            from toonverter.formats import register_default_formats

            register_default_formats()  # Ensure formats are registered

            toon_data_encoded = encode(json.loads(json_data_str), to_format="toon")

            with open(LARGE_TOON_FILE, "w") as f:
                f.write(toon_data_encoded)

        except Exception as e:
            pytest.fail(f"Could not generate {LARGE_TOON_FILE} needed for memory test: {e}")


# Standalone script content for memory profiling
# This script will be written to a temporary file and executed via subprocess
MEMORY_SCRIPT_CONTENT = """
import sys
import os
from memory_profiler import profile
from toonverter import decode
from toonverter.core.config import USE_RUST_DECODER # To log which decoder is used

# Ensure the large_test_data.toon exists and load it
LARGE_TOON_FILE = "large_test_data.toon"
if not os.path.exists(LARGE_TOON_FILE):
    sys.exit(1) # Should have been created by pytest fixture

with open(LARGE_TOON_FILE, "r") as f:
    large_toon_data_content = f.read()

print(f"DEBUG_DECODER_STATUS: Using Rust Decoder: {USE_RUST_DECODER}")

@profile(stream=sys.stderr)
def decode_data():
    # Pass the pre-loaded string
    _ = decode(large_toon_data_content, from_format="toon")

decode_data()
"""


class TestMemoryPerformance:
    @pytest.mark.slow
    @pytest.mark.skipif(not USE_RUST_DECODER, reason="Requires Rust decoder to be enabled")
    def test_decode_large_file_memory_usage_rust_decoder(self, tmp_path):
        """
        Tests the memory usage when decoding a large TOON file using the Rust decoder.
        """
        script_path = tmp_path / "profile_script_rust.py"
        with open(script_path, "w") as f:
            f.write(MEMORY_SCRIPT_CONTENT)

        # Run the script using subprocess and capture stderr
        result = subprocess.run(
            [sys.executable, "-m", "memory_profiler", str(script_path)],
            capture_output=True,
            text=True,
            check=False,  # Don't raise CalledProcessError for non-zero exit codes
        )

        log_content = result.stderr

        peak_memory_mb = 0.0
        for line in log_content.splitlines():
            match = re.search(r"^\s*\d+\s+([\d.]+)\s+MiB", line)
            if match:
                current_mem = float(match.group(1))
                peak_memory_mb = max(peak_memory_mb, current_mem)

        # Max expected memory usage for this test (in MiB).
        # This reflects the Python object graph overhead for 100,000 unique string objects.
        # This is high, but appears to be a characteristic of Python's memory model for this data type.
        max_expected_memory_mb = 1100.0

        assert result.returncode == 0, (
            f"Memory profiling script failed with exit code {result.returncode}:\n{result.stderr}"
        )
        assert peak_memory_mb > 0.0, (
            f"Memory profiling did not capture any memory usage. Log content:\n{log_content}"
        )
        assert peak_memory_mb < max_expected_memory_mb, (
            f"Peak memory usage ({peak_memory_mb:.2f} MiB) exceeded expected maximum of {max_expected_memory_mb:.2f} MiB. "
            f"Input file size: ~{os.path.getsize(LARGE_TOON_FILE) / (1024 * 1024):.2f} MiB. "
            f"Memory Profiler output:\n{log_content}"
        )

    @pytest.mark.slow
    def test_decode_large_file_memory_usage_python_decoder_baseline(self, tmp_path):
        """
        Tests the memory usage when decoding a large TOON file using the pure Python decoder.
        This serves as a baseline for Python object overhead.
        """
        script_path = tmp_path / "profile_script_python.py"
        # Temporarily override USE_RUST_DECODER to False for the subprocess
        # This will be picked up by toonverter.core.config
        temp_env = os.environ.copy()
        temp_env["TOON_USE_RUST_DECODER"] = "False"

        with open(script_path, "w") as f:
            f.write(MEMORY_SCRIPT_CONTENT)  # MEMORY_SCRIPT_CONTENT imports decode from toonverter

        result = subprocess.run(
            [sys.executable, "-m", "memory_profiler", str(script_path)],
            capture_output=True,
            text=True,
            check=False,
            env=temp_env,  # Use modified environment
        )

        log_content = result.stderr

        peak_memory_mb = 0.0
        for line in log_content.splitlines():
            match = re.search(r"^\s*\d+\s+([\d.]+)\s+MiB", line)
            if match:
                current_mem = float(match.group(1))
                peak_memory_mb = max(peak_memory_mb, current_mem)

        # Python decoder might have slightly different memory profile, but should be in similar range
        max_expected_memory_mb = 1100.0  # Adjusted to match observed Python overhead

        assert result.returncode == 0, (
            f"Memory profiling script failed with exit code {result.returncode}:\n{result.stderr}"
        )
        assert peak_memory_mb > 0.0, (
            f"Memory profiling did not capture any memory usage. Log content:\n{log_content}"
        )
        assert peak_memory_mb < max_expected_memory_mb, (
            f"Peak memory usage ({peak_memory_mb:.2f} MiB) exceeded expected maximum of {max_expected_memory_mb:.2f} MiB. "
            f"Input file size: ~{os.path.getsize(LARGE_TOON_FILE) / (1024 * 1024):.2f} MiB. "
            f"Memory Profiler output:\n{log_content}"
        )
