Schema Helpers API
============================================================

.. automodule:: toonverter.utils.schema_helpers
   :members:
   :undoc-members:
   :show-inheritance:

The ``schema_helpers`` module provides automatic schema inference and validation
for structured data.

Example Usage
-------------

Basic Schema Inference
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.utils.schema_helpers import infer_schema

    # Simple data inference
    data = {
        "name": "Alice",
        "age": 30,
        "email": "alice@example.com",
        "active": True
    }

    schema = infer_schema(data)
    
    # Access inferred field information
    print(schema["name"].type_hint)  # SchemaType.STRING
    print(schema["age"].type_hint)   # SchemaType.INTEGER

Data Validation
~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.utils.schema_helpers import infer_schema, validate_data

    # Infer schema from example
    example_data = {
        "username": "alice",
        "age": 30,
        "email": "alice@example.com"
    }
    
    schema = infer_schema(example_data)

    # Validate new data
    new_data = {
        "username": "bob",
        "age": 25,
        "email": "bob@example.com"
    }
    
    report = validate_data(new_data, schema)
    
    if report.is_valid:
        print("✓ Data is valid!")
    else:
        for error in report.errors:
            print(f"✗ {error.path}: {error.rule_failed}")

Type Detection
~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.utils.schema_helpers import get_base_type, get_broadest_type
    from toonverter.core.types import SchemaType

    # Get base type
    assert get_base_type("hello") == SchemaType.STRING
    assert get_base_type(42) == SchemaType.INTEGER
    assert get_base_type(3.14) == SchemaType.FLOAT
    assert get_base_type([]) == SchemaType.ARRAY

    # Get broadest type from a set
    types = {SchemaType.INTEGER, SchemaType.FLOAT}
    assert get_broadest_type(types) == SchemaType.FLOAT

Common Use Cases
----------------

API Response Validation
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.utils.schema_helpers import infer_schema, validate_data

    # Define expected API response
    expected_response = {
        "status": "success",
        "data": {
            "user_id": 123,
            "username": "alice"
        }
    }

    # Infer schema
    api_schema = infer_schema(expected_response)

    # Validate actual response
    actual_response = get_api_response()
    report = validate_data(actual_response, api_schema)

    if not report.is_valid:
        handle_invalid_response(report.errors)

Configuration Validation
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.utils.schema_helpers import infer_schema, validate_data
    from toonverter.core.types import SchemaValidationOptions
    import json

    # Load example config
    with open("config.example.json") as f:
        example_config = json.load(f)

    # Generate schema
    config_schema = infer_schema(example_config)

    # Validate user config
    with open("config.user.json") as f:
        user_config = json.load(f)

    options = SchemaValidationOptions(strict_type_checking=True)
    report = validate_data(user_config, config_schema, options)

    if not report.is_valid:
        print("Configuration errors:")
        for error in report.errors:
            print(f"  {error.path}: {error.rule_failed}")

Nested Data Validation
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.utils.schema_helpers import infer_schema, validate_data

    # Complex nested structure
    data = {
        "user": {
            "id": 123,
            "profile": {
                "name": "Bob",
                "settings": {"theme": "dark"}
            }
        },
        "tags": ["python", "data", "schema"]
    }

    schema = infer_schema(data)

    # Validate new nested data
    new_data = {
        "user": {
            "id": 456,
            "profile": {
                "name": "Alice",
                "settings": {"theme": "light"}
            }
        },
        "tags": ["javascript", "web"]
    }

    report = validate_data(new_data, schema)
    print(f"Valid: {report.is_valid}")

Array Validation
~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.utils.schema_helpers import infer_schema, validate_data

    # Data with arrays
    data = {
        "ids": [1, 2, 3],
        "names": ["Alice", "Bob"],
        "objects": [
            {"id": 1, "value": "a"},
            {"id": 2, "value": "b"}
        ]
    }

    schema = infer_schema(data)

    # Validate new array data
    new_data = {
        "ids": [4, 5],
        "names": ["Charlie"],
        "objects": [
            {"id": 3, "value": "c"}
        ]
    }

    report = validate_data(new_data, schema)

Advanced Features
-----------------

Validation Options
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.core.types import SchemaValidationOptions

    # Strict validation
    strict_options = SchemaValidationOptions(
        strict_type_checking=True,
        ignore_extra_fields=False
    )

    report = validate_data(data, schema, strict_options)

    # Lenient validation
    lenient_options = SchemaValidationOptions(
        strict_type_checking=False,
        ignore_extra_fields=True
    )

    report = validate_data(data, schema, lenient_options)

Handling Null Values
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.utils.schema_helpers import infer_schema

    # Data with null creates optional fields
    data_with_nulls = {
        "name": "Alice",
        "middle_name": None,  # Optional field
        "age": 30
    }

    schema = infer_schema(data_with_nulls)
    
    # middle_name is marked as not required
    assert schema["middle_name"].required == False

Type Coercion
~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.utils.schema_helpers import validate_data
    from toonverter.core.types import SchemaValidationOptions

    # Schema expects FLOAT
    schema = infer_schema({"price": 99.99})

    # Data has INTEGER
    data = {"price": 100}

    # Lenient mode allows coercion
    lenient = SchemaValidationOptions(strict_type_checking=False)
    report = validate_data(data, schema, lenient)
    assert report.is_valid  # True

Error Handling
--------------

Understanding Errors
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.utils.schema_helpers import validate_data

    schema = infer_schema({"age": 30})
    invalid_data = {"age": "thirty"}

    report = validate_data(invalid_data, schema)

    for error in report.errors:
        print(f"Path: {error.path}")
        print(f"Rule: {error.rule_failed}")
        print(f"Expected: {error.expected}")
        print(f"Actual: {error.actual}")
