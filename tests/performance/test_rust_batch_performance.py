import json
import time

import pytest

from toonverter import encode


try:
    from toonverter import convert_json_batch, convert_json_directory

    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust extension not available")
@pytest.mark.benchmark(group="batch_processing")
class TestBatchPerformance:
    @pytest.fixture(scope="class")
    def dataset_dir(self, tmp_path_factory):
        # Create a directory with many files for the whole class
        dir_path = tmp_path_factory.mktemp("perf_dataset")

        print("\nGenerating dataset...")  # noqa: T201
        # 1. 1000 small files (1KB each)
        for i in range(1000):
            data = {"id": i, "name": f"User{i}", "active": True, "padding": "x" * 50}
            with open(dir_path / f"small_{i}.json", "w") as f:
                json.dump(data, f)

        # 2. 20 HEAVY files (5MB each) = 100MB Total
        # This forces Python to allocate massive amount of objects
        large_data = [{"id": j, "val": "x" * 1000, "meta": {"a": 1, "b": 2}} for j in range(5000)]
        for i in range(20):
            with open(dir_path / f"large_{i}.json", "w") as f:
                json.dump(large_data, f)

        print("Dataset generated.")  # noqa: T201
        return dir_path

    def python_batch_process(self, paths):
        results = []
        for p in paths:
            try:
                with open(p) as f:
                    # This is the killer: loading 5MB JSON into Python dicts/lists
                    data = json.load(f)
                encoded = encode(data)
                results.append(encoded)
            except Exception:
                pass
        return results

    def test_rust_vs_python_batch_small(self, dataset_dir, benchmark):
        """Benchmark Rust vs Python for 1000 small files."""
        paths = [str(p) for p in dataset_dir.glob("small_*.json")]
        assert len(paths) == 1000

        def run_rust():
            convert_json_batch(paths, None)

        benchmark(run_rust)

        # Manual comparison
        start = time.perf_counter()
        self.python_batch_process(paths)
        py_time = time.perf_counter() - start

        start = time.perf_counter()
        convert_json_batch(paths, None)
        rust_time = time.perf_counter() - start

        print(  # noqa: T201
            f"\n[Comparison] Small Files (1000): Python={py_time:.4f}s, Rust={rust_time:.4f}s. Speedup={py_time / rust_time:.2f}x"
        )

    def test_rust_vs_python_batch_heavy(self, dataset_dir, benchmark):
        """Benchmark Rust vs Python for 20 HEAVY (5MB) files."""
        paths = [str(p) for p in dataset_dir.glob("large_*.json")]
        assert len(paths) == 20

        def run_rust():
            convert_json_batch(paths, None)

        benchmark(run_rust)

        # Manual comparison
        start = time.perf_counter()
        self.python_batch_process(paths)
        py_time = time.perf_counter() - start

        start = time.perf_counter()
        convert_json_batch(paths, None)
        rust_time = time.perf_counter() - start

        print(  # noqa: T201
            f"\n[Comparison] Heavy Files (100MB Total): Python={py_time:.4f}s, Rust={rust_time:.4f}s. Speedup={py_time / rust_time:.2f}x"
        )

    def test_rust_directory_walk(self, dataset_dir, benchmark):
        """Benchmark Rust directory walking + conversion."""
        dir_str = str(dataset_dir)

        def run_rust():
            convert_json_directory(dir_str, recursive=False, output_dir=None)

        benchmark(run_rust)

    def test_rust_write_to_disk(self, dataset_dir, tmp_path, benchmark):
        """Benchmark Rust writing to disk (streaming)."""
        paths = [str(p) for p in dataset_dir.glob("large_*.json")]
        out_dir = str(tmp_path)

        def run_rust():
            convert_json_batch(paths, out_dir)

        benchmark(run_rust)
