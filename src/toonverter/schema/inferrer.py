"""Schema Inference Engine."""

from typing import Any

from .models import SchemaField


class SchemaInferrer:
    """Infers schema from data samples."""

    def infer(self, data: Any) -> SchemaField:
        """Infer schema from a single data instance.

        Recursive function that maps Python types to SchemaFields.
        """
        if data is None:
            return SchemaField(type="null", nullable=True)

        if isinstance(data, bool):
            return SchemaField(type="boolean")

        if isinstance(data, int):
            return SchemaField(type="integer")

        if isinstance(data, float):
            return SchemaField(type="float")

        if isinstance(data, str):
            return SchemaField(type="string")

        if isinstance(data, list):
            if not data:
                return SchemaField(type="array", items=SchemaField(type="unknown"))

            # Infer schema for all items and merge them
            item_schema = self.infer(data[0])
            for item in data[1:]:
                item_schema = item_schema.merge(self.infer(item))

            return SchemaField(type="array", items=item_schema)

        if isinstance(data, dict):
            properties = {}
            for key, value in data.items():
                properties[key] = self.infer(value)
            return SchemaField(type="object", properties=properties)

        return SchemaField(type="unknown", description=str(type(data)))

    def infer_from_stream(self, iterator: Any, limit: int = 1000) -> SchemaField:
        """Infer schema from a stream of data.

        Args:
            iterator: Iterable data source
            limit: Max items to analyze

        Returns:
            Merged SchemaField representing the stream
        """
        current_schema = SchemaField(type="unknown")

        for i, item in enumerate(iterator):
            item_schema = self.infer(item)
            current_schema = current_schema.merge(item_schema)
            if i + 1 >= limit:
                break

        return current_schema
