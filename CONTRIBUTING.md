# Contributing to TOON Converter

Thank you for your interest in contributing to TOON Converter! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of Python packaging and testing

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR-USERNAME/toon-converter.git
cd toon-converter
```

3. Add upstream remote:

```bash
git remote add upstream https://github.com/yourusername/toon-converter.git
```

## Development Setup

### Install Development Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with all dependencies
make install-dev

# Or manually:
pip install -e ".[all]"
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Verify Installation

```bash
# Run tests to verify everything works
make test

# Run type checking
make type-check

# Run linting
make lint
```

## Development Workflow

### Create a Feature Branch

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
```

### Make Changes

1. Write your code following our [Coding Standards](#coding-standards)
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass
5. Ensure code is properly formatted and typed

### Run Quality Checks

```bash
# Format code
make format

# Run linter
make lint

# Run type checker
make type-check

# Run tests
make test

# Or run all checks at once
make quality
```

### Commit Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <subject>

# Types:
# - feat: New feature
# - fix: Bug fix
# - docs: Documentation changes
# - style: Code style changes (formatting, etc.)
# - refactor: Code refactoring
# - test: Test additions or changes
# - chore: Build process or auxiliary tool changes

# Examples:
git commit -m "feat(encoder): add streaming support for large files"
git commit -m "fix(decoder): handle edge case with empty arrays"
git commit -m "docs(readme): update installation instructions"
```

### Push Changes

```bash
git push origin feature/your-feature-name
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with these specifications:

- **Line Length**: 100 characters (configured in ruff)
- **Formatting**: Automated with ruff format
- **Linting**: Enforced with ruff
- **Type Hints**: Required for all public APIs

### Type Hints

```python
# ✓ Good - Full type hints
def encode(data: dict[str, Any], options: EncodeOptions) -> str:
    """Encode data to TOON format."""
    pass

# ✗ Bad - No type hints
def encode(data, options):
    pass
```

### Docstrings

We use Google-style docstrings:

```python
def convert(
    source: str,
    target: str,
    from_format: str,
    to_format: str,
    **options: Any
) -> ConversionResult:
    """Convert data from one format to another.

    Args:
        source: Path to source file
        target: Path to target file
        from_format: Source format (e.g., 'json', 'yaml')
        to_format: Target format (e.g., 'toon')
        **options: Additional conversion options

    Returns:
        ConversionResult with conversion details and statistics

    Raises:
        FileNotFoundError: If source file doesn't exist
        ConversionError: If conversion fails

    Examples:
        >>> convert('data.json', 'data.toon', 'json', 'toon')
        ConversionResult(success=True, ...)
    """
    pass
```

### Code Organization

Follow SOLID principles:

- **Single Responsibility**: Each class/function has one clear purpose
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes must be substitutable for base types
- **Interface Segregation**: Many specific interfaces over one general
- **Dependency Inversion**: Depend on abstractions, not concretions

### Error Handling

```python
# ✓ Good - Specific exceptions with context
raise ConversionError(
    f"Failed to convert {source} from {from_format} to {to_format}: {reason}"
)

# ✗ Bad - Generic exceptions
raise Exception("Conversion failed")
```

## Testing Guidelines

### Test Coverage

- **Minimum**: 95% overall coverage
- **Public API**: 100% coverage required
- **Critical Paths**: 100% coverage required

### Writing Tests

```python
# tests/unit/test_encoder.py
import pytest
from toon_converter.encoders import Encoder


class TestEncoder:
    """Test suite for TOON encoder."""

    @pytest.fixture
    def encoder(self):
        """Create encoder instance for testing."""
        return Encoder(format='toon')

    def test_encode_simple_dict(self, encoder):
        """Test encoding of simple dictionary."""
        data = {"name": "Alice", "age": 30}
        result = encoder.encode(data)
        assert "name" in result
        assert "Alice" in result

    @pytest.mark.parametrize("data,expected", [
        ({"a": 1}, "a:1"),
        ({"a": 1, "b": 2}, "a:1,b:2"),
    ])
    def test_encode_parametrized(self, encoder, data, expected):
        """Test encoding with multiple inputs."""
        result = encoder.encode(data)
        assert result == expected
```

### Test Categories

Use pytest markers:

```python
@pytest.mark.unit
def test_unit():
    """Fast, isolated unit test."""
    pass

@pytest.mark.integration
def test_integration():
    """Integration test with external dependencies."""
    pass

@pytest.mark.slow
def test_slow():
    """Slow test (e.g., large file processing)."""
    pass
```

### Running Tests

```bash
# All tests
make test

# Fast tests only
make test-fast

# Specific test file
pytest tests/unit/test_encoder.py -v

# Specific test function
pytest tests/unit/test_encoder.py::TestEncoder::test_encode_simple_dict -v

# With coverage report
make test-cov
```

## Documentation

### Update Documentation

When adding new features:

1. Add docstrings to all public APIs
2. Update README.md with examples
3. Add API documentation in `docs/api/`
4. Add user guide in `docs/guides/`
5. Update CHANGELOG.md

### Build Documentation

```bash
make docs
make serve-docs  # View at http://localhost:8000
```

## Pull Request Process

### Before Submitting

1. ✓ All tests pass (`make test`)
2. ✓ Code is formatted (`make format`)
3. ✓ Linting passes (`make lint`)
4. ✓ Type checking passes (`make type-check`)
5. ✓ Pre-commit hooks pass (`pre-commit run --all-files`)
6. ✓ Documentation is updated
7. ✓ CHANGELOG.md is updated

### Submit Pull Request

1. Push your branch to your fork
2. Create pull request on GitHub
3. Fill out the PR template completely
4. Link related issues
5. Request review from maintainers

### PR Title Format

Follow Conventional Commits:

```
feat(encoder): add streaming support for large files
fix(decoder): handle edge case with empty arrays
docs(readme): update installation instructions
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation and Context
Why is this change required? What problem does it solve?

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass locally

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added with >95% coverage
- [ ] CHANGELOG.md updated
```

### Review Process

1. Automated checks must pass (CI/CD)
2. At least one maintainer approval required
3. All review comments addressed
4. Up-to-date with main branch

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Creating a Release

Maintainers only:

```bash
# Update changelog
# Edit CHANGELOG.md to document changes

# Bump version
make release-patch   # 0.1.0 -> 0.1.1
# or
make release-minor   # 0.1.0 -> 0.2.0
# or
make release-major   # 0.1.0 -> 1.0.0

# Push changes and tags
git push && git push --tags

# Build and publish to PyPI
make build
make publish
```

## Plugin Development

### Creating a Plugin

See [Plugin Development Guide](docs/guides/plugin_development.md) for detailed instructions.

```python
# my_format_plugin/plugin.py
from toon_converter.plugins import Plugin
from toon_converter.core.interfaces import FormatAdapter

class MyFormatAdapter(FormatAdapter):
    def encode(self, data, options):
        # Implementation
        pass

    def decode(self, data_str, options):
        # Implementation
        pass

class MyFormatPlugin(Plugin):
    name = "myformat"
    version = "1.0.0"

    def register(self, registry):
        registry.register('myformat', MyFormatAdapter())
```

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/yourusername/toon-converter/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/yourusername/toon-converter/issues)
- **Security**: Email security@example.com

## Recognition

Contributors will be recognized in:

- README.md Contributors section
- Release notes
- GitHub contributors page

Thank you for contributing to TOON Converter!
