from typing import Any

import pytest

# Assuming schema_helpers is correctly imported from src
from src.toonverter.utils.schema_helpers import (
    get_base_type,
    get_broadest_type,
    infer_schema,
    validate_data,
)

# Import all necessary components for testing
from toonverter.core.types import (
    SchemaField,
    SchemaFieldDict,
    SchemaType,
    SchemaValidationOptions,
)


@pytest.fixture
def sample_data() -> dict[str, Any]:
    """Fixture for standard data used in inference tests.
    Note: Contains 'nullable_field' (None) and 'optional_field' (present)
    to cover inference paths."""
    return {
        "id": 101,
        "name": "Widget A",
        "score": 99.5,
        "is_active": True,
        "details": {"flag": True, "value": "x"},
        "tags": [1, 2, 3],
        "optional_field": "present",
        "nullable_field": None,
    }


@pytest.fixture
def validation_schema() -> SchemaFieldDict:
    """Fixture for a static schema used in validation tests."""
    return {
        "id": SchemaField(
            name="id",
            type_hint=SchemaType.INTEGER,
            allowed_types=[SchemaType.INTEGER],
            required=True,
        ),
        "name": SchemaField(
            name="name",
            type_hint=SchemaType.STRING,
            allowed_types=[SchemaType.STRING],
            required=False,
        ),
        "score": SchemaField(
            name="score",
            type_hint=SchemaType.FLOAT,
            allowed_types=[SchemaType.FLOAT],
            required=True,
        ),
        "is_active": SchemaField(
            name="is_active",
            type_hint=SchemaType.BOOLEAN,
            allowed_types=[SchemaType.BOOLEAN],
            required=True,
        ),
        "details": SchemaField(
            name="details",
            type_hint=SchemaType.OBJECT,
            allowed_types=[SchemaType.OBJECT],
            required=True,
            sub_schema={
                # flag: required, non-nullable
                "flag": SchemaField(
                    name="flag",
                    type_hint=SchemaType.BOOLEAN,
                    allowed_types=[SchemaType.BOOLEAN],
                    required=True,
                ),
                # value: optional (non-required), nullable
                "value": SchemaField(
                    name="value",
                    type_hint=SchemaType.STRING,
                    allowed_types=[SchemaType.STRING, SchemaType.NULL],
                    required=False,
                ),
            },
        ),
        "tags": SchemaField(
            name="tags",
            type_hint=SchemaType.ARRAY,
            allowed_types=[SchemaType.ARRAY],
            required=True,
            array_item_schema=SchemaField(
                name="item",
                type_hint=SchemaType.INTEGER,
                allowed_types=[SchemaType.INTEGER],
                required=True,
            ),
        ),
        "optional_field": SchemaField(
            name="optional_field",
            type_hint=SchemaType.STRING,
            allowed_types=[SchemaType.STRING],
            required=False,
        ),
        # Field required to be present, but can be NULL
        "nullable_required": SchemaField(
            name="nullable_required",
            type_hint=SchemaType.STRING,
            allowed_types=[SchemaType.STRING, SchemaType.NULL],
            required=True,
        ),
    }


# --- Type Mapping Helper Tests ---


def test_get_base_type_primitives():
    """Tests get_base_type for all primitive types and None."""
    assert get_base_type("hello") == SchemaType.STRING
    assert get_base_type(True) == SchemaType.BOOLEAN
    assert get_base_type(123) == SchemaType.INTEGER
    assert get_base_type(12.34) == SchemaType.FLOAT
    assert get_base_type(None) == SchemaType.NULL


def test_get_base_type_complex():
    """Tests get_base_type for complex types and the fallback."""
    assert get_base_type({"a": 1}) == SchemaType.OBJECT
    assert get_base_type([1, 2]) == SchemaType.ARRAY
    assert get_base_type((1, 2)) == SchemaType.ARRAY  # Tuple
    assert get_base_type({1, 2}) == SchemaType.ARRAY  # Set
    assert get_base_type(object()) == SchemaType.STRING  # Fallback case (unknown type)


def test_get_broadest_type():
    """Tests type precedence in get_broadest_type."""
    # Precedence expected (based on passed tests): FLOAT > STRING > INT > BOOL > ...
    assert get_broadest_type({SchemaType.INTEGER, SchemaType.FLOAT}) == SchemaType.FLOAT

    assert get_broadest_type({SchemaType.INTEGER, SchemaType.STRING}) == SchemaType.STRING

    assert get_broadest_type({SchemaType.BOOLEAN, SchemaType.STRING}) == SchemaType.STRING
    assert get_broadest_type({SchemaType.OBJECT, SchemaType.ARRAY}) == SchemaType.OBJECT
    assert get_broadest_type({SchemaType.BOOLEAN, SchemaType.INTEGER}) == SchemaType.INTEGER
    assert get_broadest_type(set()) == SchemaType.STRING  # Default fallback


# --- Schema Inference Tests ---


def test_infer_schema_primitives(sample_data):
    """Tests inference for basic non-null fields."""
    schema = infer_schema(sample_data)

    assert schema["id"].type_hint == SchemaType.INTEGER
    assert schema["id"].required is True
    assert schema["id"].allowed_types == [SchemaType.INTEGER]

    assert schema["score"].type_hint == SchemaType.FLOAT
    assert schema["is_active"].type_hint == SchemaType.BOOLEAN
    assert schema["name"].type_hint == SchemaType.STRING


def test_infer_schema_null_optionality():
    """Tests inference for null values (should be optional, guess STRING, allow NULL)."""
    data = {"nullable_field": None}
    schema = infer_schema(data)

    field = schema["nullable_field"]
    assert field.type_hint == SchemaType.STRING  # Guesses STRING as primary type hint
    assert field.required is False  # Must be optional
    assert SchemaType.NULL in field.allowed_types
    assert SchemaType.STRING in field.allowed_types
    assert len(field.allowed_types) == 2


def test_infer_schema_objects(sample_data):
    """Tests inference for OBJECT type and nested required fields."""
    schema = infer_schema(sample_data)
    details = schema["details"]

    assert details.type_hint == SchemaType.OBJECT
    assert details.required is True
    assert details.sub_schema is not None
    assert isinstance(details.sub_schema["flag"], SchemaField)
    assert details.sub_schema["flag"].type_hint == SchemaType.BOOLEAN

    # 'value' is 'x' in the fixture, so it must be inferred as required=True
    assert details.sub_schema["value"].required is True
    assert SchemaType.NULL not in details.sub_schema["value"].allowed_types


def test_infer_schema_nested_optional():
    """Tests inference for a field inferred as optional (NULL) inside a nested object."""
    data = {"parent": {"child_present": 1, "child_optional": None}}
    schema = infer_schema(data)
    optional_field = schema["parent"].sub_schema["child_optional"]

    assert optional_field.type_hint == SchemaType.STRING
    assert optional_field.required is False
    assert SchemaType.NULL in optional_field.allowed_types


def test_infer_schema_array_primitives(sample_data):
    """Tests inference for homogeneous array of primitives."""
    schema = infer_schema(sample_data)
    tags = schema["tags"]

    assert tags.type_hint == SchemaType.ARRAY
    assert tags.array_item_schema is not None
    assert tags.array_item_schema.type_hint == SchemaType.INTEGER
    assert tags.array_item_schema.allowed_types == [SchemaType.INTEGER]


def test_infer_schema_array_with_nulls():
    """Tests inference for array with mixed types including nulls (homogenization + NULL allowance)."""
    data = {"mixed_array": [10, "A", None, 20.5]}
    schema = infer_schema(data)
    arr = schema["mixed_array"]

    assert arr.array_item_schema.type_hint == SchemaType.FLOAT  # Broadest type is FLOAT
    assert SchemaType.NULL in arr.array_item_schema.allowed_types
    assert SchemaType.FLOAT in arr.array_item_schema.allowed_types
    assert SchemaType.INTEGER in arr.array_item_schema.allowed_types
    assert SchemaType.STRING in arr.array_item_schema.allowed_types
    assert len(arr.array_item_schema.allowed_types) == 4


def test_infer_schema_empty_array():
    """Tests inference for an empty array (should default to STRING item type)."""
    data = {"empty_arr": []}
    schema = infer_schema(data)
    arr = schema["empty_arr"]

    assert arr.array_item_schema.type_hint == SchemaType.STRING
    assert arr.array_item_schema.allowed_types == [SchemaType.STRING]


def test_infer_schema_array_of_objects():
    """Tests inference for an array of objects (merging sub-schemas)."""
    data = {
        "obj_arr": [
            {"k1": 1, "k2": "a"},
            {"k1": 2, "k3": True, "k2": None},  # Merges k3 and makes k2 optional/nullable
        ]
    }
    schema = infer_schema(data)
    arr = schema["obj_arr"]

    assert arr.array_item_schema.type_hint == SchemaType.OBJECT
    sub = arr.array_item_schema.sub_schema
    assert sub["k1"].type_hint == SchemaType.INTEGER
    assert sub["k3"].type_hint == SchemaType.BOOLEAN
    # k2 was inferred from a string, then appeared as None -> optional string
    assert sub["k2"].type_hint == SchemaType.STRING
    assert sub["k2"].required is False
    assert SchemaType.NULL in sub["k2"].allowed_types


def test_infer_schema_root_data_error():
    """Tests that infer_schema raises TypeError for non-mapping root data."""
    with pytest.raises(TypeError, match="Schema inference only supports dictionary"):
        infer_schema([1, 2, 3])


# --- Validation Success Tests ---


def test_validation_valid_data(validation_schema):
    """
    Tests validation passes for data that exactly matches the schema.
    Uses clean data to avoid Extra Field error from sample_data fixture.
    """
    data = {
        "id": 101,
        "name": "Widget A",
        "score": 99.5,
        "is_active": True,
        # 'value': None is allowed because it is required=False and allows NULL
        "details": {"flag": True, "value": None},
        "tags": [1, 2, 3],
        "optional_field": "present",  # Present optional field
        "nullable_required": None,  # Null value for required, nullable field
    }
    report = validate_data(data, validation_schema)
    assert report.is_valid is True
    assert len(report.errors) == 0


def test_validation_coercion_success(validation_schema):
    """Tests successful type coercion when strict_type_checking is False (default)."""
    data = {
        "id": 100.0,  # FLOAT-as-INT in INTEGER field (Coercion)
        "name": "Test",
        "score": 50,  # INT in FLOAT field (Coercion)
        "is_active": True,
        "details": {"flag": True, "value": "x"},
        "tags": [1, 2, 3],
        "nullable_required": None,  # Null allowed
        "optional_field": "present",
    }
    options = SchemaValidationOptions(strict_type_checking=False)
    report = validate_data(data, validation_schema, options)
    assert report.is_valid is True
    assert len(report.errors) == 0


def test_validation_missing_optional_field(validation_schema):
    """Tests validation passes when an optional field is missing."""
    data = {
        "id": 101,
        "score": 99.5,
        "is_active": True,
        "details": {"flag": True, "value": "x"},
        "tags": [1, 2, 3],
        "nullable_required": "ok",
    }
    report = validate_data(data, validation_schema)
    assert report.is_valid is True
    assert len(report.errors) == 0


# --- Validation Failure Tests (Type Mismatches) ---


def test_validation_type_mismatch_primitive(validation_schema):
    """Tests type mismatch failure for primitives."""
    data = {
        "id": "A101",  # STRING in INTEGER field
        "name": 123,  # INTEGER in STRING field
        "score": 99.5,
        "is_active": "maybe",  # STRING in BOOLEAN field
        "details": {"flag": True},
        "tags": [1, 2, 3],
        "optional_field": "present",
        "nullable_required": "ok",
    }
    report = validate_data(data, validation_schema)
    assert report.is_valid is False
    assert len(report.errors) == 3
    # Check that the errors are correctly identified
    error_paths = {e.path for e in report.errors}
    assert "$.id" in error_paths
    assert "$.name" in error_paths
    assert "$.is_active" in error_paths


def test_validation_array_item_type_mismatch(validation_schema):
    """Tests type mismatch failure inside an array."""
    data = {
        "id": 101,
        "name": "Widget A",
        "score": 99.5,
        "is_active": True,
        "details": {"flag": True},
        "tags": [1, "two", 3],  # STRING item in INTEGER array
        "optional_field": "present",
        "nullable_required": "ok",
    }
    report = validate_data(data, validation_schema)
    assert report.is_valid is False
    assert len(report.errors) == 1
    assert report.errors[0].path == "$.tags[1]"
    assert report.errors[0].rule_failed == "Type Mismatch"


def test_validation_nested_required_null(validation_schema):
    """Tests failure for required nested field being null."""
    data = {
        "id": 101,
        "name": "Widget A",
        "score": 99.5,
        "is_active": True,
        "details": {"flag": None, "value": "x"},  # Required field 'flag' is null
        "tags": [1, 2, 3],
        "optional_field": "present",
        "nullable_required": "ok",
    }
    # 'flag' is required and does not allow NULL
    report = validate_data(data, validation_schema)
    assert report.is_valid is False
    assert len(report.errors) == 1
    assert report.errors[0].path == "$.details.flag"
    assert report.errors[0].rule_failed == "Required Field is Null"


def test_validation_null_in_not_allowed_field(validation_schema):
    """Tests failure for null value in a field that does not explicitly allow NULL."""
    # Optional field 'optional_field' does not list NULL in allowed_types
    data = {
        "id": 101,
        "name": "Widget A",
        "score": 99.5,
        "is_active": True,
        "details": {"flag": True, "value": "x"},
        "tags": [1, 2, 3],
        "optional_field": None,  # Null value in a non-required, non-nullable field
        "nullable_required": "ok",
    }
    report = validate_data(data, validation_schema)
    assert report.is_valid is False
    assert len(report.errors) == 1
    assert report.errors[0].path == "$.optional_field"
    assert report.errors[0].rule_failed == "Type Mismatch"


# --- Validation Failure Tests (Required/Extra) ---


def test_validation_missing_required_field(validation_schema):
    """Tests validation fails when a required field is missing."""
    data = {
        # "id": 101, <-- Missing required field
        "name": "Widget A",
        "score": 99.5,
        "is_active": True,
        "details": {"flag": True, "value": "x"},
        "tags": [1, 2, 3],
        "optional_field": "present",
        "nullable_required": "ok",
    }
    report = validate_data(data, validation_schema)
    assert report.is_valid is False
    assert len(report.errors) == 1
    assert report.errors[0].path == "$.id"
    assert report.errors[0].rule_failed == "Missing Required Field"


def test_validation_extra_fields_in_strict_mode(validation_schema):
    """Tests failure when an extra field is present and ignore_extra_fields is False (default)."""
    data = {
        "id": 101,
        "name": "Widget A",
        "score": 99.5,
        "is_active": True,
        "details": {"flag": True, "value": "x"},
        "tags": [1, 2, 3],
        "optional_field": "present",
        "nullable_required": "ok",
        "new_root_field": "extra value",  # Extra field
    }
    options = SchemaValidationOptions(ignore_extra_fields=False)
    report = validate_data(data, validation_schema, options)
    assert report.is_valid is False
    assert len(report.errors) == 1
    assert report.errors[0].path == "$.new_root_field"
    assert report.errors[0].rule_failed == "Extra Field Not Allowed"


def test_validation_ignore_extra_fields_mode(validation_schema):
    """Tests validation passes when an extra field is present and ignore_extra_fields is True."""
    data = {
        "id": 101,
        "name": "Widget A",
        "score": 99.5,
        "is_active": True,
        "details": {"flag": True, "value": "x"},
        "tags": [1, 2, 3],
        "optional_field": "present",
        "nullable_required": "ok",
        "new_root_field": "extra value",
    }
    options = SchemaValidationOptions(ignore_extra_fields=True)
    report = validate_data(data, validation_schema, options)
    assert report.is_valid is True
    assert len(report.errors) == 0


# --- Validation Strictness Tests ---


def test_validation_coercion_failure_in_strict_mode(validation_schema):
    """Tests that coercion fails when strict_type_checking is True."""
    data = {
        "id": 100.0,  # FLOAT-as-INT in INTEGER field (Coercion fails in strict mode)
        "name": "Test",
        "score": 50,  # INT in FLOAT field (Coercion fails in strict mode)
        "is_active": True,
        "details": {"flag": True, "value": "x"},
        "tags": [1, 2, 3],
        "optional_field": "present",
        "nullable_required": "ok",
    }
    options = SchemaValidationOptions(strict_type_checking=True)
    report = validate_data(data, validation_schema, options)
    assert report.is_valid is False
    assert len(report.errors) == 2
    error_paths = {e.path for e in report.errors}
    assert "$.id" in error_paths
    assert "$.score" in error_paths


def test_validation_non_int_float_coercion_failure(validation_schema):
    """Tests a standard type mismatch involving non-integer floats (should fail even without strict mode)."""
    data = {
        "id": 101.5,  # Non-integer FLOAT in INTEGER field (Always fails)
        "name": "Test",
        "score": 99.5,
        "is_active": True,
        "details": {"flag": True, "value": "x"},
        "tags": [1, 2, 3],
        "optional_field": "present",
        "nullable_required": "ok",
    }
    report = validate_data(data, validation_schema)
    assert report.is_valid is False
    assert len(report.errors) == 1
    assert report.errors[0].path == "$.id"
    assert report.errors[0].actual == SchemaType.FLOAT.value


# --- Root Validation Tests ---


def test_validation_root_data_error(validation_schema):
    """Tests validation fails when the root data is not a mapping."""
    data = [1, 2, 3]  # List instead of Dict

    report = validate_data(data, validation_schema)
    assert report.is_valid is False
    assert len(report.errors) == 1
    assert report.errors[0].path == "$"
    assert report.errors[0].rule_failed == "Root Data Type"
    assert report.errors[0].actual == SchemaType.ARRAY.value
