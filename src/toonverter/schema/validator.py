"""Schema Validator."""

from typing import Any

from .models import SchemaField


class ValidationError(Exception):
    """Base class for validation errors."""


class SchemaValidator:
    """Validates data against a TOON Schema."""

    def validate(self, data: Any, schema: SchemaField, strict: bool = False) -> list[str]:
        """Validate data against schema.

        Returns:
            List of error messages. Empty list implies valid.
        """
        errors: list[str] = []
        self._validate_recursive(data, schema, "$", errors, strict)
        return errors

    def _validate_recursive(
        self, data: Any, schema: SchemaField, path: str, errors: list[str], strict: bool
    ) -> None:
        # 1. Null check
        if data is None:
            if not schema.nullable and schema.type != "null":
                errors.append(f"{path}: Expected {schema.type}, got null")
            return

        # 2. Type check
        if schema.type == "unknown":
            return  # Unknown accepts anything

        if schema.type == "union":
            # Check if data matches ANY of the union types
            valid_union = False
            for subtype in schema.union_types:
                sub_errors: list[str] = []
                self._validate_recursive(data, subtype, path, sub_errors, strict)
                if not sub_errors:
                    valid_union = True
                    break
            if not valid_union:
                errors.append(f"{path}: Data does not match any of the union types")
            return

        # Strict type checking to avoid bool matching int
        is_valid = False
        if schema.type == "string":
            is_valid = isinstance(data, str)
        elif schema.type == "integer":
            is_valid = isinstance(data, int) and not isinstance(data, bool)
        elif schema.type == "float":
            is_valid = isinstance(data, (float, int)) and not isinstance(data, bool)
        elif schema.type == "boolean":
            is_valid = isinstance(data, bool)
        elif schema.type == "array":
            is_valid = isinstance(data, list)
        elif schema.type == "object":
            is_valid = isinstance(data, dict)
        else:
            # Fallback for custom types if any
            is_valid = True

        if not is_valid:
            errors.append(f"{path}: Expected {schema.type}, got {type(data).__name__}")
            return

        # 3. Recursive checks
        if schema.type == "array":
            if schema.items:
                for i, item in enumerate(data):
                    self._validate_recursive(item, schema.items, f"{path}[{i}]", errors, strict)

        if schema.type == "object":
            # Check required fields
            for key, prop_schema in schema.properties.items():
                if prop_schema.required and key not in data:
                    errors.append(f"{path}: Missing required field '{key}'")

            # Check property types
            for key, value in data.items():
                if key in schema.properties:
                    self._validate_recursive(
                        value, schema.properties[key], f"{path}.{key}", errors, strict
                    )
                elif strict:
                    # Strict mode: no extra fields allowed
                    errors.append(f"{path}: Unknown field '{key}'")
