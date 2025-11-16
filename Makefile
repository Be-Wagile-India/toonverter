.PHONY: help install install-dev clean test test-cov test-fast lint format type-check pre-commit build release docs serve-docs benchmark

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
RUFF := $(PYTHON) -m ruff
MYPY := $(PYTHON) -m mypy
BUMP := bump2version
SRC_DIR := src/toonverter
TEST_DIR := tests

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package in production mode
	$(PIP) install -e .

install-dev: ## Install package with development dependencies
	$(PIP) install -e ".[all]"
	$(PIP) install -r requirements-dev.txt
	pre-commit install

clean: ## Remove build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

test: ## Run all tests with coverage
	$(PYTEST) -v

test-cov: ## Run tests with detailed coverage report
	$(PYTEST) -v --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing

test-fast: ## Run tests in parallel without coverage
	$(PYTEST) -v -n auto --no-cov

test-unit: ## Run unit tests only
	$(PYTEST) -v -m unit

test-integration: ## Run integration tests only
	$(PYTEST) -v -m integration

lint: ## Run ruff linter
	$(RUFF) check $(SRC_DIR) $(TEST_DIR)

lint-fix: ## Run ruff linter with auto-fix
	$(RUFF) check --fix $(SRC_DIR) $(TEST_DIR)

format: ## Format code with ruff
	$(RUFF) format $(SRC_DIR) $(TEST_DIR)

format-check: ## Check code formatting without changes
	$(RUFF) format --check $(SRC_DIR) $(TEST_DIR)

type-check: ## Run mypy type checker
	$(MYPY) $(SRC_DIR)

pre-commit: ## Run all pre-commit hooks
	pre-commit run --all-files

quality: lint type-check test ## Run all quality checks (lint, type-check, test)

build: clean ## Build distribution packages
	$(PYTHON) -m build

release-patch: ## Bump patch version and create release
	$(BUMP) patch
	@echo "Patch version bumped. Review changes and run 'git push && git push --tags'"

release-minor: ## Bump minor version and create release
	$(BUMP) minor
	@echo "Minor version bumped. Review changes and run 'git push && git push --tags'"

release-major: ## Bump major version and create release
	$(BUMP) major
	@echo "Major version bumped. Review changes and run 'git push && git push --tags'"

publish-test: build ## Publish to Test PyPI
	$(PYTHON) -m twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI (production)
	$(PYTHON) -m twine upload dist/*

docs: ## Build documentation
	cd docs && $(PYTHON) -m sphinx -b html . _build/html

serve-docs: docs ## Build and serve documentation locally
	cd docs/_build/html && $(PYTHON) -m http.server 8000

benchmark: ## Run performance benchmarks
	$(PYTEST) benchmarks/ -v --benchmark-only

profile: ## Profile code performance
	$(PYTHON) -m cProfile -o profile.prof -m pytest tests/
	$(PYTHON) -m pstats profile.prof

check: lint type-check test-fast ## Quick check before commit (lint, type-check, fast tests)

init: install-dev ## Initialize development environment
	@echo "Development environment initialized successfully!"
	@echo "Run 'make test' to verify everything works."

ci: lint type-check test ## Run CI pipeline locally
	@echo "CI checks completed successfully!"
