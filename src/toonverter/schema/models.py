"""Data models for the Schema Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


# Supported data types in TOON schema
SchemaType = Literal[
    "string", "integer", "float", "boolean", "null", "array", "object", "unknown", "union"
]


@dataclass
class SchemaField:
    """Definition of a field in the schema.

    Represents the structure, type, and constraints of a data element.
    Recursive definition allows modeling complex nested structures.

    Attributes:
        type: Primary data type
        nullable: Whether None/null is allowed
        required: Whether the field must be present (for object properties)
        items: Schema for array items (if type is array)
        properties: Schema for object properties (if type is object)
        description: Optional description or statistics
        union_types: List of allowed types if type is 'union'
    """

    type: SchemaType
    nullable: bool = False
    required: bool = True
    items: SchemaField | None = None
    properties: dict[str, SchemaField] = field(default_factory=dict)
    description: str | None = None
    union_types: list[SchemaField] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize schema to dictionary."""
        data: dict[str, Any] = {"type": self.type}

        if self.nullable:
            data["nullable"] = True
        if not self.required:
            data["required"] = False
        if self.description:
            data["description"] = self.description

        if self.type == "array" and self.items:
            data["items"] = self.items.to_dict()

        if self.type == "object" and self.properties:
            data["properties"] = {k: v.to_dict() for k, v in self.properties.items()}

        if self.type == "union" and self.union_types:
            data["anyOf"] = [t.to_dict() for t in self.union_types]

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SchemaField:
        """Deserialize schema from dictionary."""
        field_type = data.get("type", "unknown")
        instance = cls(
            type=field_type,
            nullable=data.get("nullable", False),
            required=data.get("required", True),
            description=data.get("description"),
        )

        if field_type == "array" and "items" in data:
            instance.items = cls.from_dict(data["items"])

        if field_type == "object" and "properties" in data:
            instance.properties = {k: cls.from_dict(v) for k, v in data["properties"].items()}

        if field_type == "union" and "anyOf" in data:
            instance.union_types = [cls.from_dict(t) for t in data["anyOf"]]

        return instance

    def merge(self, other: SchemaField) -> SchemaField:
        """Merge this schema with another, widening types as necessary.

        This is the core logic for schema inference.
        """
        # 1. Handle Unknowns (widening)
        if self.type == "unknown":
            return other
        if other.type == "unknown":
            return self

        # 2. Handle Nullability
        if other.type == "null":
            self.nullable = True
            return self
        if self.type == "null":
            other.nullable = True
            return other

        new_nullable = self.nullable or other.nullable

        # 3. Handle Type Mismatch -> Union or Promotion
        if self.type != other.type:
            # numeric promotion: int + float -> float
            if {self.type, other.type} == {"integer", "float"}:
                return SchemaField(type="float", nullable=new_nullable)

            # Otherwise create/update union
            # (Simplification: For now, if mismatch, just return Union of types)
            # This logic needs to be robust for recursive unions.
            # For production MVP, we can return a 'union' type containing both.
            return self._merge_into_union(other, new_nullable)

        # 4. Handle Matching Types (Recursion)
        if self.type == "array":
            # Merge array items
            if self.items and other.items:
                new_items = self.items.merge(other.items)
                return SchemaField(type="array", items=new_items, nullable=new_nullable)
            if self.items:
                return self
            return other

        if self.type == "object":
            # Merge properties
            all_keys = set(self.properties.keys()) | set(other.properties.keys())
            new_props = {}
            for key in all_keys:
                prop_a = self.properties.get(key)
                prop_b = other.properties.get(key)

                if prop_a and prop_b:
                    new_props[key] = prop_a.merge(prop_b)
                elif prop_a:
                    # Key missing in 'other', so it's not required
                    prop_a.required = False
                    new_props[key] = prop_a
                # Key missing in 'self', so it's not required
                # prop_b is guaranteed to be not None here
                elif prop_b:
                    prop_b.required = False
                    new_props[key] = prop_b

            return SchemaField(type="object", properties=new_props, nullable=new_nullable)

        if self.type == "union":
            return self._merge_into_union(other, new_nullable)

        # Primitive types match
        return SchemaField(type=self.type, nullable=new_nullable)

    def _merge_into_union(self, other: SchemaField, nullable: bool) -> SchemaField:
        """Helper to merge two schemas into a union."""
        types = []

        # Collect types from self
        if self.type == "union":
            types.extend(self.union_types)
        else:
            types.append(self)

        # Collect types from other
        if other.type == "union":
            types.extend(other.union_types)
        else:
            types.append(other)

        # Deduplicate types (simple check)
        unique_types = []
        seen_types = set()
        for t in types:
            # We only check primary type for simple dedup
            # A robust production system would deep compare schemas
            if t.type not in seen_types:
                unique_types.append(t)
                seen_types.add(t.type)

        return SchemaField(type="union", union_types=unique_types, nullable=nullable)
