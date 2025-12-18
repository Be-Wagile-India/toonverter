"""Memory performance tests for the Streaming Decoder."""

import gc
import logging
import os
from collections.abc import Iterator

from memory_profiler import memory_usage

from toonverter.decoders.stream_decoder import StreamDecoder


# Setup logger
logger = logging.getLogger(__name__)


def generate_massive_toon_item(num_fields: int) -> str:
    """Generate a single TOON list item with many fields."""
    lines = ["- "]
    for i in range(num_fields):
        lines.append(f"  field{i}: value{i}\n")
    return "".join(lines)


def massive_toon_stream(num_items: int, fields_per_item: int) -> Iterator[str]:
    """Generate a massive TOON stream."""
    yield f"[{num_items}]:\n"
    for _ in range(num_items):
        yield generate_massive_toon_item(fields_per_item)


def test_streaming_memory_usage():
    """
    Compare memory usage between legacy decode_stream and new items() method.
    We increase size to ensure we hit measurable thresholds.
    """
    # Use environment variable to allow quick local runs vs slow CI
    is_ci = os.environ.get("CI") == "true"
    num_items = 2 if is_ci else 10
    fields_per_item = 2000 if is_ci else 10000

    decoder = StreamDecoder()

    def run_legacy():
        gc.collect()
        stream = massive_toon_stream(num_items, fields_per_item)
        count = 0
        for _item in decoder.decode_stream(stream):
            count += 1
        return count

    def run_new_items_full():
        gc.collect()
        stream = massive_toon_stream(num_items, fields_per_item)
        count = 0
        for _item in decoder.items(stream):
            count += 1
        return count

    def run_event_streaming():
        gc.collect()
        stream = massive_toon_stream(num_items, fields_per_item)
        count = 0
        for _ev, _val in decoder.items(stream, events=True):
            count += 1
        return count

    # Measure memory
    mem_legacy = max(memory_usage(run_legacy))
    mem_new_full = max(memory_usage(run_new_items_full))
    mem_events = max(memory_usage(run_event_streaming))

    logger.info("\nMemory Usage (Max):")
    logger.info("  Legacy decode_stream: %.2f MiB", mem_legacy)
    logger.info("  New items():          %.2f MiB", mem_new_full)
    logger.info("  Event items():        %.2f MiB", mem_events)

    assert mem_events <= mem_legacy * 1.1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_streaming_memory_usage()
