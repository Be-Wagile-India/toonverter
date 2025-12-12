Changelog
============================================================

All notable changes to this project are documented here.

For the full detailed changelog, see the `CHANGELOG.md <https://github.com/Be-Wagile-India/toonverter/blob/main/CHANGELOG.md>`_ file in the repository root.

Latest Releases
---------------

Version 1.0.3 (2025-12-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Added**

*   Rust-accelerated encoding and decoding for enhanced performance.
*   Configurable parallelism for Python encoders, allowing thresholds for parallel processing of large collections.
*   Truly streaming output for Python encoders, supporting `io.TextIOBase` objects to reduce memory usage for large outputs.
*   Initial implementation of `PyToonBuffer` (Rust pyclass) to explore zero-copy Python types (though currently disabled).

**Changed**

*   Updated documentation to reflect Rust integration.

**Fixed**

*   Minor linting and type-checking issues in Python codebase.


Version 1.0.2 (2025-01-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Added**

* Logo added to README.md and documentation
* GitHub Pages documentation deployment workflow
* AUTHORS.md file with contributor information
* Comprehensive test coverage verification
* Documentation for all 10 framework integrations

**Changed**

* Updated documentation URLs to GitHub Pages
* Improved README with logo and better formatting
* Enhanced Sphinx documentation configuration

**Fixed**

* PyPI package links now correctly point to Be-Wagile-India repository
* Documentation build configuration optimized
* Missing documentation files added

Version 1.0.1 (2025-01-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Fixed**

* Package metadata and repository links
* Documentation configuration

Version 1.0.0 (2025-01-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Initial Production Release**

* Complete TOON v2.0 Specification Implementation
* 10 Framework Integrations (Pandas, Pydantic, LangChain, FastAPI, SQLAlchemy, MCP, LlamaIndex, Haystack, DSPy, Instructor)
* 554 tests with 50.66% code coverage
* Token Analysis & Optimization tools
* Three-Tier API Architecture
* CLI Tools with rich output
* Comprehensive documentation

For full release notes and older versions, see the `complete changelog <https://github.com/Be-Wagile-India/toonverter/blob/main/CHANGELOG.md>`_.
