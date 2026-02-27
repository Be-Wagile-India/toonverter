"""
Example 19: Memory-Efficient Streaming

This example demonstrates how to use the StreamDecoder to process massive TOON 
datasets with near-zero memory footprint.
"""

import io
import itertools
from toonverter import StreamDecoder
from toonverter.decoders.event_parser import ParserEvent
from toonverter.encoders.stream_encoder import StreamList, ToonStreamEncoder

def demonstrate_item_streaming():
    print("--- 1. Item-by-Item Streaming ---")
    # Simulate a large TOON array with 1000 items
    # In a real scenario, this would be a large file on disk
    toon_input = ["[1000]:\n"] + [f"- item_{i}: value_{i}\n" for i in range(1000)]
    
    decoder = StreamDecoder()
    
    # Process items one-by-one
    # Only one 'item' is in memory at any given time
    count = 0
    for item in decoder.items(iter(toon_input)):
        count += 1
        if count <= 3:
            print(f"Decoded item {count}: {item}")
    
    print(f"Successfully processed {count} items.\n")

def demonstrate_event_streaming():
    print("--- 2. Low-Level Event Streaming ---")
    # For massive nested objects where even a single item might be too large,
    # use events=True to get raw parsing events.
    toon_input = [
        "[*]:\n",
        '- name: "Big Document"\n',
        "  metadata:\n",
        "    id: 12345\n",
        "    tags[2]: tag1, tag2\n"
    ]
    
    decoder = StreamDecoder()
    
    print("Parsing events:")
    for event, value in decoder.items(iter(toon_input), events=True):
        if event == ParserEvent.KEY:
            print(f"  Field: {value}")
        elif event == ParserEvent.VALUE:
            print(f"  Value: {value}")
        elif event == ParserEvent.START_OBJECT:
            print("  { Start Object }")
        elif event == ParserEvent.END_OBJECT:
            print("  { End Object }")
        elif event == ParserEvent.START_ARRAY:
            print(f"  [ Start Array (length={value}) ]")
        elif event == ParserEvent.END_ARRAY:
            print("  ] End Array [")
    print()

def demonstrate_indefinite_encoding():
    print("--- 3. Indefinite Stream Encoding ---")
    # You can also stream output for infinite generators
    infinite_gen = itertools.count(start=1)
    
    # Signify indefinite length with length=None
    stream_data = StreamList(iterator=infinite_gen, length=None)
    
    encoder = ToonStreamEncoder()
    
    print("Encoded stream (first 5 chunks):")
    chunk_count = 0
    for chunk in encoder.iterencode(stream_data):
        print(chunk, end="")
        chunk_count += 1
        if chunk_count > 10:  # Stop early for demonstration
            break
    print("\n... (stream continues indefinitely) ...")

if __name__ == "__main__":
    demonstrate_item_streaming()
    demonstrate_event_streaming()
    demonstrate_indefinite_encoding()
