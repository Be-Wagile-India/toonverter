"""Tests for the Schema Engine."""

from toonverter.schema import SchemaField, SchemaInferrer, SchemaValidator


class TestSchemaInference:
    def test_infer_simple_types(self):
        inferrer = SchemaInferrer()
        assert inferrer.infer("hello").type == "string"
        assert inferrer.infer(42).type == "integer"
        assert inferrer.infer(3.14).type == "float"
        assert inferrer.infer(True).type == "boolean"
        assert inferrer.infer(None).type == "null"

    def test_infer_list_merging(self):
        inferrer = SchemaInferrer()
        # List of mixed int and float -> should become float
        data = [1, 2.5, 3]
        schema = inferrer.infer(data)
        assert schema.type == "array"
        assert schema.items.type == "float"

    def test_infer_object_merging(self):
        inferrer = SchemaInferrer()
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob"},  # Missing age
        ]
        schema = inferrer.infer_from_stream(data)

        assert schema.type == "object"
        assert schema.properties["name"].type == "string"
        assert schema.properties["name"].required is True

        # Age should be optional because it was missing in one record
        assert schema.properties["age"].type == "integer"
        assert schema.properties["age"].required is False

    def test_infer_union_types(self):
        inferrer = SchemaInferrer()
        data = ["string", 123]
        schema = inferrer.infer(data)
        # Assuming default merging creates union for disparate types
        assert schema.type == "array"
        assert schema.items.type == "union"
        assert len(schema.items.union_types) == 2
        types = {t.type for t in schema.items.union_types}
        assert "string" in types
        assert "integer" in types

    def test_merge_two_unions(self):
        # Manually test merge logic
        schema1 = SchemaField(type="union", union_types=[SchemaField(type="integer")])
        schema2 = SchemaField(type="union", union_types=[SchemaField(type="string")])

        merged = schema1.merge(schema2)
        assert merged.type == "union"
        assert len(merged.union_types) == 2
        types = {t.type for t in merged.union_types}
        assert "integer" in types
        assert "string" in types

    def test_merge_type_into_union(self):
        schema1 = SchemaField(type="union", union_types=[SchemaField(type="integer")])
        schema2 = SchemaField(type="string")

        merged = schema1.merge(schema2)
        assert merged.type == "union"
        assert len(merged.union_types) == 2

        # Reverse merge
        merged_reverse = schema2.merge(schema1)
        assert merged_reverse.type == "union"
        assert len(merged_reverse.union_types) == 2

    def test_merge_arrays_missing_items(self):
        # Array with defined items
        schema1 = SchemaField(type="array", items=SchemaField(type="integer"))
        # Generic array (no items defined)
        schema2 = SchemaField(type="array")

        # Merge 1 with 2 -> should keep items
        merged1 = schema1.merge(schema2)
        assert merged1.type == "array"
        assert merged1.items.type == "integer"

        # Merge 2 with 1 -> should take items
        merged2 = schema2.merge(schema1)
        assert merged2.type == "array"
        assert merged2.items.type == "integer"


class TestSchemaValidation:
    def test_validate_simple(self):
        validator = SchemaValidator()
        schema = SchemaField(type="integer")

        assert not validator.validate(42, schema)
        assert validator.validate("not an int", schema)

    def test_validate_object_required(self):
        validator = SchemaValidator()
        schema = SchemaField(
            type="object",
            properties={
                "id": SchemaField(type="integer", required=True),
                "name": SchemaField(type="string", required=False),
            },
        )

        assert not validator.validate({"id": 1, "name": "A"}, schema)
        assert not validator.validate({"id": 2}, schema)

        errors = validator.validate({"name": "No ID"}, schema)
        assert len(errors) == 1
        assert "Missing required field 'id'" in errors[0]

    def test_validate_strict_mode(self):
        validator = SchemaValidator()
        schema = SchemaField(type="object", properties={"a": SchemaField(type="integer")})

        # Extra field 'b'
        data = {"a": 1, "b": 2}

        # Not strict -> Valid
        assert not validator.validate(data, schema, strict=False)

        # Strict -> Invalid
        errors = validator.validate(data, schema, strict=True)
        assert len(errors) == 1
        assert "Unknown field 'b'" in errors[0]

    def test_validate_union(self):
        validator = SchemaValidator()
        schema = SchemaField(
            type="union", union_types=[SchemaField(type="integer"), SchemaField(type="string")]
        )

        assert not validator.validate(123, schema)
        assert not validator.validate("abc", schema)
        assert validator.validate(True, schema)  # Bool is not int/str

    def test_validate_nested_array(self):
        validator = SchemaValidator()
        schema = SchemaField(type="array", items=SchemaField(type="integer"))

        assert not validator.validate([1, 2, 3], schema)
        errors = validator.validate([1, "two", 3], schema)
        assert len(errors) == 1
        assert "Expected integer" in errors[0]


class TestSchemaSerialization:
    def test_roundtrip_simple(self):
        schema = SchemaField(type="integer", nullable=True, description="An ID")
        data = schema.to_dict()
        assert data["type"] == "integer"
        assert data["nullable"] is True
        assert data["description"] == "An ID"

        restored = SchemaField.from_dict(data)
        assert restored.type == schema.type
        assert restored.nullable == schema.nullable
        assert restored.description == schema.description

    def test_roundtrip_nested(self):
        schema = SchemaField(
            type="object",
            properties={"users": SchemaField(type="array", items=SchemaField(type="string"))},
        )
        data = schema.to_dict()
        assert data["properties"]["users"]["type"] == "array"

        restored = SchemaField.from_dict(data)
        assert restored.type == "object"
        assert "users" in restored.properties
        assert restored.properties["users"].items.type == "string"

    def test_roundtrip_union(self):
        schema = SchemaField(
            type="union", union_types=[SchemaField(type="integer"), SchemaField(type="boolean")]
        )
        data = schema.to_dict()
        assert "anyOf" in data
        assert len(data["anyOf"]) == 2

        restored = SchemaField.from_dict(data)
        assert restored.type == "union"
        assert len(restored.union_types) == 2
