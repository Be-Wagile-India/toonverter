from collections.abc import Iterable, Mapping
from typing import Any

from toonverter.core.types import (
    ArrayItemSchema,
    SchemaField,
    SchemaFieldDict,
    SchemaInferenceOptions,
    SchemaType,
    SchemaValidationOptions,
    ValidationError,
    ValidationReport,
)


# --- Type Mapping Helpers ---


def get_base_type(value: Any) -> SchemaType:
    """Infers the most fundamental SchemaType from a Python value."""
    if isinstance(value, str):
        return SchemaType.STRING
    if isinstance(value, bool):
        return SchemaType.BOOLEAN
    if isinstance(value, int):
        return SchemaType.INTEGER
    if isinstance(value, float):
        # Note: If it's a float, it stays float. Validation handles int-in-float flexibility.
        return SchemaType.FLOAT
    if isinstance(value, Mapping):
        return SchemaType.OBJECT
    if isinstance(value, Iterable) and not isinstance(value, str):
        # Lists, tuples, sets are treated as ARRAY for schema purposes. Exclude str.
        return SchemaType.ARRAY
    if value is None:
        return SchemaType.NULL

    # Fallback for complex or unknown types
    return SchemaType.STRING


def get_broadest_type(types: set[SchemaType]) -> SchemaType:
    """Determines the single broadest type for a set of types.

    The order determines precedence: FLOAT > STRING > INTEGER > BOOLEAN > (OBJECT/ARRAY).
    """
    if SchemaType.FLOAT in types:
        return SchemaType.FLOAT
    if SchemaType.STRING in types:
        return SchemaType.STRING
    if SchemaType.INTEGER in types:
        return SchemaType.INTEGER
    if SchemaType.BOOLEAN in types:
        return SchemaType.BOOLEAN
    if SchemaType.OBJECT in types:
        return SchemaType.OBJECT
    if SchemaType.ARRAY in types:
        return SchemaType.ARRAY
    return SchemaType.STRING  # Default fallback


# --- Schema Inference Logic ---


def _infer_field_schema(value: Any, name: str, options: SchemaInferenceOptions) -> SchemaField:
    """Infers the SchemaField structure for a single value."""
    inferred_type = get_base_type(value)

    sub_schema: SchemaFieldDict | None = None
    array_item_schema: ArrayItemSchema = None

    # Handle NULL/Optional fields consistently.
    if inferred_type == SchemaType.NULL:
        # Fields inferred from NULL must be optional (required=False).
        # We guess the type as STRING (safe default) and explicitly allow STRING and NULL.
        return SchemaField(
            name=name,
            type_hint=SchemaType.STRING,
            allowed_types=[SchemaType.STRING, SchemaType.NULL],
            required=False,
        )

    # For non-NULL fields:
    # 1. They are assumed required (required=True).
    # 2. allowed_types MUST contain the primary inferred type.
    allowed_types = [inferred_type]

    if inferred_type == SchemaType.OBJECT:
        sub_schema = infer_schema(value, options)

    elif (
        inferred_type == SchemaType.ARRAY
    ):  # Check for array without checking Iterable again, as get_base_type did it
        item_types: set[SchemaType] = set()

        # Collect types from all items
        for item in value:
            item_types.add(get_base_type(item))

        # Remove NULL from the set of types before determining the primary type,
        # but keep track if nulls were present.
        null_was_present = SchemaType.NULL in item_types
        item_types.discard(SchemaType.NULL)

        item_allowed_types: list[SchemaType] = []

        if not item_types:
            # Array is empty or only contained nulls. Default to STRING items.
            item_allowed_types = [SchemaType.STRING]
            primary_item_type = SchemaType.STRING
        else:
            # Determine the item's primary type (homogenization)
            primary_item_type = get_broadest_type(item_types)
            item_allowed_types = list(item_types)

        # If nulls were present, explicitly allow NULL for array items
        if null_was_present:
            item_allowed_types.append(SchemaType.NULL)

        # Remove duplicates
        item_allowed_types = list(set(item_allowed_types))

        if primary_item_type == SchemaType.OBJECT:
            # Must recursively infer a combined schema if objects are present
            combined_sub_schema: dict[str, SchemaField] = {}
            for item in value:
                if isinstance(item, Mapping):
                    current_schema = infer_schema(item, options)
                    # Simple merge (using update): fields in later objects override earlier ones
                    combined_sub_schema.update(current_schema)

            array_item_schema = SchemaField(
                name="item",
                type_hint=primary_item_type,
                allowed_types=item_allowed_types,
                sub_schema=combined_sub_schema,
                required=True,  # Item itself is required if array is non-null
            )
        else:
            # Primitive array item
            array_item_schema = SchemaField(
                name="item",
                type_hint=primary_item_type,
                allowed_types=item_allowed_types,
                required=True,  # Item itself is required if array is non-null
            )

    return SchemaField(
        name=name,
        type_hint=inferred_type,
        # CRUCIAL FIX: For non-null fields, allowed_types is just the inferred type.
        allowed_types=allowed_types,
        required=True,  # Inferred from a non-null value
        sub_schema=sub_schema,
        array_item_schema=array_item_schema,
    )


def infer_schema(data: Any, options: SchemaInferenceOptions | None = None) -> SchemaFieldDict:
    """
    Infers a SchemaField dictionary structure from the input dictionary data.

    Note: The input data must be a dictionary (the root object).
    """
    if options is None:
        options = SchemaInferenceOptions()

    if not isinstance(data, Mapping):
        # Fixed EM101: Assign error message to a variable
        error_msg = "Schema inference only supports dictionary (object) as root data."
        raise TypeError(error_msg)

    inferred_schema: SchemaFieldDict = {}

    for key, value in data.items():
        inferred_schema[key] = _infer_field_schema(value, key, options)

    return inferred_schema


# --- Validation Logic ---


def _validate_field(
    data: Any,
    schema_field: SchemaField,
    path: str,
    options: SchemaValidationOptions,
    errors: list[ValidationError],
) -> None:
    """Recursive helper for field-level validation."""

    # Check for NULL/Optionality
    if data is None:
        if schema_field.required and SchemaType.NULL not in schema_field.allowed_types:
            errors.append(
                ValidationError(
                    path=path,
                    rule_failed="Required Field is Null",
                    expected=f"Non-null {schema_field.type_hint.value}",
                    actual="null",
                )
            )
        # If NULL is present but not in allowed_types (even if not required)
        elif SchemaType.NULL not in schema_field.allowed_types:
            errors.append(
                ValidationError(
                    path=path,
                    rule_failed="Type Mismatch",
                    expected=f"Non-null type from {', '.join(t.value for t in schema_field.allowed_types)}",
                    actual="null",
                )
            )
        return

    actual_type = get_base_type(data)
    expected_type = schema_field.type_hint

    # 1. Type Check (Handle coersion/strictness)
    type_is_valid = False

    # Check against explicit allowed_types first
    if actual_type in schema_field.allowed_types:
        type_is_valid = True

    # Check for coersion (e.g., int-in-float) if not strict
    elif not options.strict_type_checking:
        # Allows INTEGER data if FLOAT is allowed
        if (
            SchemaType.FLOAT in schema_field.allowed_types and actual_type == SchemaType.INTEGER
        ) or (
            SchemaType.INTEGER in schema_field.allowed_types
            and actual_type == SchemaType.FLOAT
            and data == int(data)
        ):
            type_is_valid = True

    # Fallback check (should be covered by allowed_types, but kept for robustness)
    elif expected_type == actual_type:
        type_is_valid = True

    if not type_is_valid:
        errors.append(
            ValidationError(
                path=path,
                rule_failed="Type Mismatch",
                expected=f"One of: {', '.join(t.value for t in schema_field.allowed_types)}",
                actual=actual_type.value,
            )
        )
        return  # Stop validation for this path if type is fundamentally wrong

    # 2. Nested Validation (OBJECT)
    if expected_type == SchemaType.OBJECT and schema_field.sub_schema:
        _validate_object(data, schema_field.sub_schema, path, options, errors)

    # 3. Nested Validation (ARRAY)
    # Note: We rely on the type check above ensuring data is iterable if expected_type is ARRAY
    elif expected_type == SchemaType.ARRAY and schema_field.array_item_schema:
        item_schema = schema_field.array_item_schema
        for index, item in enumerate(data):
            _validate_field(item, item_schema, f"{path}[{index}]", options, errors)


def _validate_object(
    data: dict[str, Any],
    schema: SchemaFieldDict,
    root_path: str,
    options: SchemaValidationOptions,
    errors: list[ValidationError],
) -> None:
    """Validates dictionary data against a schema at a given path."""

    data_keys = set(data.keys())

    # 1. Check for missing required fields and validate existing fields
    for key, field_schema in schema.items():
        current_path = f"{root_path}.{key}"

        if key not in data_keys:
            if field_schema.required:
                errors.append(
                    ValidationError(
                        path=current_path,
                        rule_failed="Missing Required Field",
                        expected=field_schema.type_hint.value,
                        actual="not present",
                    )
                )
            continue  # Move to next schema key

        # Validate present field
        _validate_field(data[key], field_schema, current_path, options, errors)

    # 2. Check for extra fields (if strict mode is enabled)
    if not options.ignore_extra_fields:
        schema_keys = set(schema.keys())
        extra_keys = data_keys - schema_keys

        for key in extra_keys:
            errors.append(
                ValidationError(
                    path=f"{root_path}.{key}",
                    rule_failed="Extra Field Not Allowed",
                    expected="Field not defined in schema",
                    actual="present",
                )
            )


def validate_data(
    data: dict[str, Any], schema: SchemaFieldDict, options: SchemaValidationOptions | None = None
) -> ValidationReport:
    """
    Validates dictionary data against a SchemaField dictionary.

    Returns:
        A ValidationReport summarizing the process.
    """
    if options is None:
        options = SchemaValidationOptions()

    errors: list[ValidationError] = []

    if not isinstance(data, Mapping):
        errors.append(
            ValidationError(
                path="$",
                rule_failed="Root Data Type",
                expected="OBJECT",
                actual=get_base_type(data).value,
            )
        )
        return ValidationReport(is_valid=False, schema_used=schema, errors=errors)

    _validate_object(data, schema, "$", options, errors)

    return ValidationReport(is_valid=not errors, schema_used=schema, errors=errors)
