Testing
============================================================

TOON Converter employs a comprehensive testing strategy that covers both its Python and Rust components to ensure reliability, performance, and correctness.

Python Testing
--------------

The Python codebase is tested using `pytest`. These tests cover the high-level API, modular components (encoders, decoders, analysis), framework integrations, and various edge cases.

### Running Python Tests

You can run all Python tests using the `Makefile`:

.. code-block:: bash

   make test

This command executes all Python tests, including unit and integration tests.

To run tests with a coverage report:

.. code-block:: bash

   make test-cov

You can also run specific test files or functions using `pytest` directly:

.. code-block:: bash

   pytest tests/unit/test_encoder.py -v
   pytest tests/unit/test_encoder.py::TestEncoder::test_encode_simple_dict -v

Rust Testing
------------

The Rust core is tested using Rust's built-in test framework (`cargo test`). These tests focus on the low-level logic, performance-critical sections, and direct Rust functionality exposed via `PyO3`.

### Running Rust Tests

To execute all Rust tests:

.. code-block:: bash

   cd rust
   cargo test
   cd ..

Integration of Python and Rust Tests
------------------------------------

Python integration tests may interact with the Rust extension to verify its behavior from the Python side. However, isolated Rust unit tests ensure the core Rust logic is sound before integration. This dual-layered approach helps maintain the stability and performance of the mixed-language codebase.

See root directory files for details.