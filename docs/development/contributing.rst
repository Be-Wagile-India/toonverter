Contributing
============================================================

We welcome contributions from the community! This guide will help you get started.

For detailed contributing guidelines, see the `CONTRIBUTING.md <https://github.com/Be-Wagile-India/toonverter/blob/main/CONTRIBUTING.md>`_ file in the repository root.

Quick Start
-----------

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a new branch** for your feature or bugfix
4. **Make your changes** with tests
5. **Run the test suite** to ensure everything works
6. **Submit a pull request** with a clear description

Development Setup
-----------------

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/Be-Wagile-India/toonverter.git
   cd toonverter

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install in development mode with all dependencies
   pip install -e ".[all,dev]"

   # Install pre-commit hooks
   pre-commit install

Running Tests
-------------

.. code-block:: bash

   # Run all tests
   pytest

   # Run with coverage
   pytest --cov=toonverter --cov-report=html

   # Run specific test file
   pytest tests/unit/test_encoder.py

   # Run tests in parallel
   pytest -n auto

Code Quality
------------

We use several tools to maintain code quality:

* **ruff**: Linting and formatting
* **mypy**: Static type checking
* **pytest**: Testing framework
* **pre-commit**: Git hooks for code quality

.. code-block:: bash

   # Format code
   ruff format src/ tests/

   # Check linting
   ruff check src/ tests/

   # Type checking
   mypy src/

Authors & Contributors
----------------------

See the `AUTHORS.md <https://github.com/Be-Wagile-India/toonverter/blob/main/AUTHORS.md>`_ file for a list of contributors.

**Project Lead**: Danesh Patel (danesh_patel@outlook.com)

**Organization**: Be-Wagile India

Contribution Areas
------------------

We welcome contributions in many areas:

* **Code**: New features, bug fixes, performance improvements
* **Documentation**: Improvements to docs, examples, tutorials
* **Testing**: New tests, test coverage improvements
* **Integrations**: New framework integrations (e.g., Haystack, DSPy)
* **Bug Reports**: Detailed bug reports with reproduction steps
* **Feature Requests**: Well-described feature proposals

How to Report Bugs
------------------

1. Check if the bug has already been reported in `GitHub Issues <https://github.com/Be-Wagile-India/toonverter/issues>`_
2. Create a new issue with:

   * Clear, descriptive title
   * Steps to reproduce
   * Expected vs actual behavior
   * Python version and OS
   * Code samples if applicable

How to Request Features
------------------------

1. Check if the feature has already been requested
2. Create a new issue with:

   * Clear description of the feature
   * Use case and motivation
   * Possible implementation approach
   * Examples of how it would be used

Code Review Process
-------------------

1. All submissions require review
2. Maintainers will review your PR within a few days
3. Address any feedback or requested changes
4. Once approved, your PR will be merged

License
-------

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank You!
----------

Your contributions make this project better for everyone. We appreciate your time and effort!
