Architecture
============================================================

TOON Converter's architecture is designed for performance, flexibility, and maintainability.
It primarily consists of a Python core with an optional Rust extension for critical paths.

Python Core
-----------

The majority of the library is implemented in Python, providing:

*   **High-level API**: User-friendly facade for encoding, decoding, conversion, and analysis.
*   **Modular Design**: Clear separation of concerns into sub-modules (encoders, decoders, analysis, integrations).
*   **Extensibility**: Plugin system and custom adapter interfaces allow easy extension.
*   **Integrations**: Seamless integration with popular Python frameworks (Pandas, Pydantic, LangChain, etc.).

Rust Extension
--------------

For performance-critical encoding and decoding operations, an optional Rust extension is provided.
This extension is built using `PyO3`, a framework for Rust bindings to the Python interpreter.

The Rust core currently focuses on:

*   **Fast Encoding**: Accelerating the conversion of Python data to TOON format.
*   **Fast Decoding**: Speeding up the parsing of TOON format into Python data structures.

Benefits of the Rust Extension:

*   **Native Performance**: Achieves near C-like speeds for complex data processing.
*   **Zero-copy Potential**: Enables future optimizations to directly reference Rust-managed memory in Python, reducing overhead.
*   **Concurrency**: Leverages Rust's efficient concurrency primitives for parallel processing where applicable.

Interaction between Python and Rust
-----------------------------------

The Python and Rust components interact via `PyO3`. Python modules call Rust functions
as if they were native Python code. Data is efficiently passed between the two languages,
with efforts made to minimize serialization/deserialization overhead.

The Rust extension is designed to be optional. If not installed or disabled, the library
gracefully falls back to its pure Python implementations.

High-Level Component Diagram
----------------------------

.. mermaid::

    graph TD
        A[User Application] --> B(Python Facade API);
        B --> C{Python Core};
        C --> D{Python Encoders/Decoders};
        D -- "Optional Fallback" --> P1[Pure Python Impl];
        D -- "PyO3 Bindings" --> R1{Rust Extension};
        R1 --> R2(Rust Encoders/Decoders);
        P1 -- "TOON Data" --> E[External Systems];
        R2 -- "TOON Data" --> E;
        C --> F{Analysis/Integrations/Plugins};
        F -- "Data" --> E;

    Note: The Rust Extension is primarily used for encoding/decoding performance.

Future Considerations
---------------------

*   Expand Rust coverage to other performance-sensitive areas (e.g., advanced parsing, complex data transformations).
*   Further optimize data transfer between Python and Rust.

See root directory files for details.