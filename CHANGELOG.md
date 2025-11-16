# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Future enhancements will be listed here

## [1.0.0] - 2025-01-17

### Added
- **Complete TOON v2.0 Specification Implementation**
  - Full encoder/decoder with all three array forms (inline, tabular, list)
  - Key folding support for nested objects
  - Canonical number formatting (no exponents, no trailing zeros)
  - Proper string escaping and quoting rules
  - Delimiter support (comma, pipe, tab)

- **Format Adapters**
  - JSON adapter with pretty-printing support
  - YAML adapter with flow/block styles
  - TOML adapter with table formatting
  - CSV adapter for tabular data
  - XML adapter with attribute handling
  - TOON native format adapter

- **Token Analysis & Optimization**
  - TiktokenCounter with multi-model support (GPT-4, GPT-3.5, Davinci)
  - FormatComparator for cross-format analysis
  - Token usage reporting with recommendations
  - Savings calculation and optimization suggestions

- **Three-Tier API Architecture**
  - Level 1 Facade API: Simple functions for common tasks (encode, decode, convert)
  - Level 2 OOP API: Stateful classes for advanced use (Encoder, Decoder, Converter, Analyzer)
  - Full type hints for IDE support

- **Comprehensive Test Suite**
  - 550+ unit tests with 50%+ coverage
  - Spec compliance tests validating TOON v2.0 conformance
  - Integration tests for format adapters
  - Performance benchmark suite
  - All critical paths tested

- **Developer Experience**
  - Modern src/ layout with proper packaging
  - Ruff for linting and formatting
  - Pre-commit hooks for code quality
  - Comprehensive documentation with examples
  - Makefile for common tasks
  - Type checking with mypy

- **Integrations Framework**
  - Plugin system with entry point discovery
  - Integration stubs for LangChain, Pandas, Pydantic, FastAPI, etc.
  - Extensible adapter registry

### Fixed
- Decoder now correctly handles all TOON v2.0 syntax
- Number encoding properly handles edge cases (NaN, Infinity, -0)
- String encoding correctly escapes special characters
- Tabular array detection and encoding

## [0.1.0] - 2025-01-15

### Added
- Initial release of TOON Converter
- Support for JSON, YAML, TOML, CSV formats
- Basic TOON encoding and decoding
- Token analysis with tiktoken
- Command-line interface
- Python 3.10+ support
- MIT License
- Documentation and examples


