# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Additional framework integrations
- Performance optimizations
- Enhanced CLI features

## [1.0.2] - 2025-01-17

### Added
- GitHub Pages documentation deployment workflow
- AUTHORS.md file with contributor information
- Comprehensive test coverage verification
- Documentation for all 10 framework integrations

### Changed
- Updated documentation URLs to GitHub Pages
- Improved README with logo and better formatting
- Enhanced Sphinx documentation configuration

### Fixed
- PyPI package links now correctly point to Be-Wagile-India repository
- Documentation build configuration optimized
- Missing documentation files added

## [## [Unreleased]] - 2025-01-17

### Fixed
- Package metadata and repository links
- Documentation configuration

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

- **10 Framework Integrations**
  - Pandas: DataFrame optimization with tabular encoding
  - Pydantic: BaseModel serialization with validation
  - LangChain: Document and Message support for RAG systems
  - FastAPI: Native TOON response class
  - SQLAlchemy: ORM model serialization and bulk operations
  - MCP: Model Context Protocol server with 4 tools
  - LlamaIndex: Node and Document support
  - Haystack: Document integration for pipelines
  - DSPy: Example and prediction support
  - Instructor: Response model integration

- **Comprehensive Test Suite**
  - 554 tests with 50.66% code coverage
  - 26/26 TOON v2.0 spec compliance tests passing
  - Integration tests for all format adapters
  - Performance benchmark suite
  - All critical paths tested

- **Developer Experience**
  - Modern src/ layout with PEP 517/518 packaging
  - Ruff for linting and formatting
  - Pre-commit hooks for code quality
  - Comprehensive documentation with examples
  - Makefile for common development tasks
  - Type checking with mypy (100% typed)

- **CLI Tools**
  - Command-line interface for file conversion
  - Token analysis from command line
  - Format validation and inspection
  - Rich output formatting

### Fixed
- Decoder correctly handles all TOON v2.0 syntax
- Number encoding handles edge cases (NaN, Infinity, -0)
- String encoding correctly escapes special characters
- Tabular array detection and encoding optimized

## [0.1.0] - 2025-01-15

### Added
- Initial development release
- Basic TOON encoding and decoding
- Support for JSON, YAML, TOML formats
- Token analysis with tiktoken
- Python 3.10+ support
- MIT License

[Unreleased]: https://github.com/Be-Wagile-India/toonverter/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/Be-Wagile-India/toonverter/compare/v## [Unreleased]...v1.0.2
[## [Unreleased]]: https://github.com/Be-Wagile-India/toonverter/compare/v1.0.0...v## [Unreleased]
[1.0.0]: https://github.com/Be-Wagile-India/toonverter/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/Be-Wagile-India/toonverter/releases/tag/v0.1.0
